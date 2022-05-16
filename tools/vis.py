import os

for k, v in os.environ.items():
    if k.startswith("QT_") and "cv2" in v:
        del os.environ[k]

import math

import PyQt5
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QSizePolicy,
    QScrollArea,
    QMessageBox,
    QMainWindow,
    QMenu,
    QAction,
    qApp,
    QFileDialog,
    QInputDialog,
)

import pylab
from numpy import pi, sin, cos, mgrid
from mpl_toolkits.mplot3d import Axes3D


# import pyqtgraph as pg
import trimesh

# os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
# QApplication.setHighDpiScaleFactorRoundingPolicy(
#     PyQt5.QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
# )


import numpy as np

# import qimage2ndarray
import cv2
import scipy

import matplotlib.pyplot as plt
import skimage

from prepare import Prep

# from preprocess_utils import HUnorm


def toQimage(img):
    h, w, _ = img.shape
    qimage = QImage(img.data, w, h, 3 * w, QImage.Format_RGB888)
    return qimage


class QImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scan = None
        self.label = None
        self.gt = None
        self.curr_slice_idx = None
        self.ww = 200
        self.wc = 0
        self.transparency = 0.8
        self.no_wwwc = False

        self.printer = QPrinter()
        self.scaleFactor = 0.0

        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setVisible(False)

        self.setCentralWidget(self.scrollArea)

        self.createActions()
        self.createMenus()

        self.setWindowTitle("MedicalSeg Visulization Tool")
        self.resize(800, 600)

    def turn_slice(self, delta):
        curr_slice_idx = self.curr_slice_idx + delta

        if self.scan is None and self.label is None:
            QMessageBox.information(self, "Image Viewer", f"No scan or label")
            return

        max_slice_idx = max(
            self.scan.shape[2] if self.scan is not None else 0,
            self.label.shape[2] if self.label is not None else 0,
        )
        if curr_slice_idx < 0 or curr_slice_idx >= max_slice_idx:
            QMessageBox.information(
                self,
                "Image Viewer",
                f"Cannot turn to slice {curr_slice_idx}, total slice {self.scan.shape[2]}",
            )
            return

        print("turninig to ", curr_slice_idx)

        self.curr_slice_idx = curr_slice_idx

        if self.scan is None:
            scan_color = np.zeros((self.label.shape[0], self.label.shape[1], 3), dtype="uint8")
        else:
            scan_color = cv2.cvtColor(self.windowlize(), cv2.COLOR_GRAY2RGB)

        if self.label is None:
            label_color = np.zeros_like(scan_color, dtype="uint8")
        else:
            label_slice = self.label[:, :, self.curr_slice_idx]
            label_color = np.zeros((self.label.shape[0], self.label.shape[1], 3), dtype="uint8")
            label_color[label_slice == 1, :] = [255, 0, 0]
            label_color[label_slice == 2, :] = [0, 255, 0]
        print(
            "blending",
            scan_color.shape,
            scan_color.dtype,
            label_color.shape,
            label_color.dtype,
            self.transparency,
        )

        # image = qimage2ndarray.array2qimage(image)
        if self.label is not None:
            image = cv2.addWeighted(scan_color, 1, label_color, 1 - self.transparency, 0)
        else:
            image = scan_color
        print("image.shape", image.shape)

        image = toQimage(image)
        if image.isNull():
            QMessageBox.information(self, "Image Viewer", f"image is null")
            return

        self.imageLabel.setPixmap(QPixmap.fromImage(image))

        self.scrollArea.setVisible(True)
        self.printAct.setEnabled(True)
        self.fitToWindowAct.setEnabled(True)
        self.updateActions()

        if not self.fitToWindowAct.isChecked():
            self.imageLabel.adjustSize()

        self.scaleFactor = 1
        print(self.scan.shape[0] if self.scan is not None else self.label.shape[0])
        self.scaleImage(
            700 / (self.scan.shape[0] if self.scan is not None else self.label.shape[0])
        )

    def windowlize(self):
        if not self.no_wwwc:
            image = self.scan[:, :, self.curr_slice_idx]
            min = self.wc - self.ww // 2
            max = self.wc + self.ww // 2
            image = image.astype("float")
            image = np.clip(image, min, max)
        image = (image - image.min()) / (image.max() - image.min()) * 255
        return image.astype("uint8")

    def change_transparency(self):
        new_transparency, done = QInputDialog.getText(self, "Change Transparency", "Transparency")
        if done:
            try:
                new_transparency = float(new_transparency)
            except:
                QMessageBox.information(self, "Image Viewer", f"Invalid Transparency")
                return
            self.transparency = np.clip(new_transparency, 0, 1)
            print("new transparency", self.transparency)
        self.turn_slice(0)

    def change_wc(self):
        new_wc, done = QInputDialog.getText(self, "Change Window Center", "Window Center")

        if done:
            try:
                new_wc = int(new_wc)
            except:
                QMessageBox.information(self, "Image Viewer", f"Invalid Window Center")
                return
            # self.transparency = np.clip(new_wc, 0, 1)
            self.wc = new_wc
            print("new wc", self.wc)
        self.turn_slice(0)

    def change_ww(self):
        new_ww, done = QInputDialog.getText(self, "Change Window Width", "Window Width")

        if done:
            try:
                new_ww = int(new_ww)
            except:
                QMessageBox.information(self, "Image Viewer", f"Invalid Window Width")
                return

            self.ww = new_ww
            print("new wc", self.ww)
        self.turn_slice(0)

    def open_label(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "QFileDialog.getOpenFileName()",
            "",
            "Label (*.gz *.nii *.dcm *.npy)",
            options=options,
        )
        print("fileName", fileName)
        if fileName is None or len(fileName) == 0:
            return
        if fileName.endswith("nii.gz"):
            self.label = Prep.load_medical_data(fileName)[0]
        else:
            self.label = np.load(fileName)
        self.label = np.rot90(self.label)

        if self.scan is not None and self.scan.shape != self.label.shape:
            zoom = np.array(self.scan.shape) / np.array(self.label.shape)
            self.label = scipy.ndimage.zoom(self.label, zoom, order=1)
            print("resize label", self.scan.shape, self.label.shape)

        if self.curr_slice_idx is None:
            self.curr_slice_idx = self.label.shape[2] // 2

        self.label = self.label.astype("uint8")
        # self.label = self.label[:, ::-1, :]
        self.turn_slice(0)

    def open_gt(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "Open Ground Truth Label",
            "",
            "Ground Truth Label (*.gz *.nii *.dcm *.npy)",
            options=options,
        )
        print("fileName", fileName)
        if fileName is None or len(fileName) == 0:
            return
        if fileName.endswith("nii.gz"):
            self.gt = Prep.load_medical_data(fileName)[0]
        else:
            self.gt = np.load(fileName)
        self.gt = np.rot90(self.gt)

        # if self.scan is not None and self.scan.shape != self.label.shape:
        #     zoom = np.array(self.scan.shape) / np.array(self.label.shape)
        #     self.label = scipy.ndimage.zoom(self.label, zoom, order=1)
        #     print("resize label", self.scan.shape, self.label.shape)

        # if self.curr_slice_idx is None:
        #     self.curr_slice_idx = self.label.shape[2] // 2

        self.gt = self.gt.astype("uint8")
        # self.turn_slice(0)

    def open_scan(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "QFileDialog.getOpenFileName()",
            "",
            "Scan (*.gz *.nii *.dcm *.npy)",
            options=options,
        )
        print("fileName", fileName)
        if fileName is None or len(fileName) == 0:
            return
        if fileName.endswith("nii.gz"):
            self.scan = Prep.load_medical_data(fileName)[0]
        else:
            self.scan = np.load(fileName)

        self.scan = np.rot90(self.scan)
        # self.scan = self.scan[:, ::-1, :]
        self.curr_slice_idx = self.scan.shape[2] // 2

        print("scan:", self.scan.shape, self.scan.min(), self.scan.max())
        self.turn_slice(0)

    # def vis_3d(self):
    #     if self.label is None and self.gt is None:
    #         return
    #     colors = [[255, 0, 0, 255], [0, 255, 0, 255]]

    #     scene = trimesh.Scene()
    #     axis = trimesh.creation.axis(origin_size=10, origin_color=[1.0, 0, 0])
    #     scene.add_geometry(axis)
    #     if self.label is not None:
    #         label = self.label
    #         print("+_+_+", label.max())

    #         for label_idx, face_color in zip(range(1, label.max() + 1), colors):
    #             label_part = label.copy()
    #             print(label_idx)
    #             label_part[label_part != label_idx] = 0
    #             verts, faces, vertex_normals, values = skimage.measure.marching_cubes(label_part)
    #             mesh = trimesh.Trimesh(
    #                 vertices=verts,
    #                 faces=faces,
    #                 vertex_normals=vertex_normals,
    #                 face_colors=face_color,
    #             )
    #             scene.add_geometry(mesh)

    #     scene.show()

    def vis_3d(self):
        if self.label is None and self.gt is None:
            return
        colors = [[255, 0, 0, 255], [0, 255, 0, 255]]

        scene = trimesh.Scene()
        axis = trimesh.creation.axis(origin_size=10, origin_color=[1.0, 0, 0])
        scene.add_geometry(axis)

        # visual = trimesh.visual.ColorVisuals(face_colors=[255, 0, 0, 255], vertex_colors=[255, 0, 0, 255])
        # print("visual.transparency", visual.transparency)
        if self.label is not None:
            verts, faces, vertex_normals, values = skimage.measure.marching_cubes(self.label)
            # print(faces.shape)
            label_mesh = trimesh.Trimesh(
                vertices=verts,
                faces=faces,
                vertex_normals=vertex_normals,
                face_colors=np.tile(np.array([255, 0, 0, 255]), (faces.shape[0], 1)),
                vertex_colors=[255, 0, 0, 255],
                # visual=visual,
            )
            # print("transparency", label_mesh.transparency)
            scene.add_geometry(label_mesh)
        self.gt = np.pad(self.label, ((0, 0), (0, 0), (5, 0)))
        if self.gt is not None:
            gt = self.gt
            verts, faces, vertex_normals, values = skimage.measure.marching_cubes(self.gt)
            gt_mesh = trimesh.Trimesh(
                vertices=verts,
                faces=faces,
                vertex_normals=vertex_normals,
                face_colors=np.tile(np.array([0, 255, 0, 255]), (faces.shape[0], 1)),
                # face_colors=[0, 255, 0, 255],
                vertex_colors=[0, 255, 0, 255],
                # visual=visual,
            )
            scene.add_geometry(gt_mesh)

        scene.show()

    # def vis_3d(self):
    #     if self.label is None and self.gt is None:
    #         return
    #     colors = [[255, 0, 0], [0, 255, 0]]
    #     fig = pylab.figure()
    #     ax = Axes3D( fig )
    #     ax.set_axis_off()

    #     if self.label is not None:
    #         label = self.label
    #         verts, faces, vertex_normals, values = skimage.measure.marching_cubes(label)
    #         ax.plot_trisurf(verts[:, 0], verts[:, 1], faces, verts[:, 2], linewidth=0 )
    #     pylab.show()

    def next_slice(self):
        print("next_slice")
        self.turn_slice(1)

    def prev_slice(self):
        print("prev_slice")
        self.turn_slice(-1)

    def createActions(self):
        self.openScanAct = QAction(
            "&Open Scan...", self, shortcut="Ctrl+O", triggered=self.open_scan
        )
        self.openLabelAct = QAction(
            "&Open Label...", self, shortcut="Ctrl+Shift+O", triggered=self.open_label
        )
        self.openGtAct = QAction(
            "&Open Ground Truth...", self, shortcut="Ctrl+Shift+I", triggered=self.open_gt
        )
        self.printAct = QAction(
            "&Print...", self, shortcut="Ctrl+P", enabled=False, triggered=self.print_
        )
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.zoomInAct = QAction(
            "Zoom &In (25%)", self, shortcut="Ctrl++", enabled=False, triggered=self.zoomIn
        )
        self.zoomOutAct = QAction(
            "Zoom &Out (25%)", self, shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut
        )
        self.normalSizeAct = QAction(
            "&Normal Size", self, shortcut="Ctrl+S", enabled=False, triggered=self.normalSize
        )
        self.fitToWindowAct = QAction(
            "&Fit to Window",
            self,
            enabled=False,
            checkable=True,
            shortcut="Ctrl+F",
            triggered=self.fitToWindow,
        )
        self.aboutAct = QAction("&About", self, triggered=self.about)
        self.aboutQtAct = QAction("About &Qt", self, triggered=qApp.aboutQt)

        self.nextSliceAct = QAction("&Next Slice", self, shortcut="W", triggered=self.next_slice)
        self.prevSliceAct = QAction("&Prev Slice", self, shortcut="S", triggered=self.prev_slice)
        self.changeTransparencyAct = QAction(
            "&Change Transparency", self, triggered=self.change_transparency
        )
        self.changeWcAct = QAction("&Change Window Center", self, triggered=self.change_wc)
        self.changeWwAct = QAction("&Change Window Width", self, triggered=self.change_ww)
        self.vis3dAct = QAction("&3D View", self, triggered=self.vis_3d)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openScanAct)
        self.fileMenu.addAction(self.openLabelAct)
        self.fileMenu.addAction(self.openGtAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.nextSliceAct)
        self.viewMenu.addAction(self.prevSliceAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.changeTransparencyAct)
        self.viewMenu.addAction(self.changeWcAct)
        self.viewMenu.addAction(self.changeWwAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.vis3dAct)

        self.transformMenu = QMenu("&Transform", self)
        self.transformMenu.addAction(QAction("&Crop to Foreground", self, triggered=self.vis_3d))
        self.transformMenu.addAction(QAction("&Reorient", self, triggered=self.vis_3d))
        self.transformMenu.addAction(QAction("&Resample 128", self, triggered=self.vis_3d))
        self.transformMenu.addAction(QAction("&Normalize", self, triggered=self.vis_3d))
        self.transformMenu.addAction(QAction("&Rotate", self, triggered=self.vis_3d))
        self.transformMenu.addAction(QAction("&Flip - Left Right", self, triggered=self.vis_3d))
        self.transformMenu.addAction(QAction("&Flip - Up Down", self, triggered=self.vis_3d))
        self.transformMenu.addAction(QAction("&Resize Crop", self, triggered=self.vis_3d))

        self.inferenceMenu = QMenu("&Inference", self)
        # self.transformMenu.addAction(QAction("&Resize Crop", self, triggered=self.vis_3d))

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.transformMenu)
        self.menuBar().addMenu(self.inferenceMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 10)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.1)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(
            int(factor * scrollBar.value() + ((factor - 1) * scrollBar.pageStep() / 2))
        )

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()

    def print_(self):
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabel.pixmap().size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabel.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())

    def about(self):
        QMessageBox.about(
            self,
            "About Image Viewer",
            "<p>The <b>Image Viewer</b> example shows how to combine "
            "QLabel and QScrollArea to display an image. QLabel is "
            "typically used for displaying text, but it can also display "
            "an image. QScrollArea provides a scrolling view around "
            "another widget. If the child widget exceeds the size of the "
            "frame, QScrollArea automatically provides scroll bars.</p>"
            "<p>The example demonstrates how QLabel's ability to scale "
            "its contents (QLabel.scaledContents), and QScrollArea's "
            "ability to automatically resize its contents "
            "(QScrollArea.widgetResizable), can be used to implement "
            "zooming and scaling features.</p>"
            "<p>In addition the example shows how to use QPainter to "
            "print an image.</p>",
        )


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    imageViewer = QImageViewer()
    imageViewer.show()
    sys.exit(app.exec_())
    # TODO QScrollArea support mouse
    # base on https://github.com/baoboa/pyqt5/blob/master/examples/widgets/imageviewer.py
    #
    # if you need Two Image Synchronous Scrolling in the window by PyQt5 and Python 3
    # please visit https://gist.github.com/acbetter/e7d0c600fdc0865f4b0ee05a17b858f2
