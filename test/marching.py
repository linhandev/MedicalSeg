#!/usr/bin/env python

# noinspection PyUnresolvedReferences
import vtkmodules.vtkInteractionStyle
# noinspection PyUnresolvedReferences
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonCore import (
    VTK_VERSION_NUMBER,
    vtkVersion
)
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkFiltersCore import (
    vtkFlyingEdges3D,
    vtkMarchingCubes
)
from vtkmodules.vtkIOImage import vtkNIFTIImageReader
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)

from vtkmodules.vtkFiltersCore import (
    vtkDecimatePro,
    vtkTriangleFilter
)

def main():
    # vtkFlyingEdges3D was introduced in VTK >= 8.2
    use_flying_edges = vtk_version_ok(8, 2, 0)

    # 1. read in label
    volume = vtkImageData()
    file_name = "/git/coronacases_001.nii.gz"
    reader = vtkNIFTIImageReader()
    reader.SetFileName(file_name)
    reader.Update()
    volume.DeepCopy(reader.GetOutput())

    if use_flying_edges:
        try:
            print("using flying edges")
            surface = vtkFlyingEdges3D()
        except AttributeError:
            surface = vtkMarchingCubes()
    else:
        surface = vtkMarchingCubes()

    surface.SetInputData(volume)
    surface.ComputeNormalsOn()
    surface.SetValue(1, 1) # 不知道什么意思
    surface.SetValue(2, 2)

    print(surface)

    renderer = vtkRenderer()
    colors = vtkNamedColors()
    renderer.SetBackground(colors.GetColor3d('DarkSlateGray'))

    render_window = vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetWindowName('MarchingCubes')

    interactor = vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)

    mapper = vtkPolyDataMapper()
    mapper.SetInputConnection(surface.GetOutputPort())
    mapper.ScalarVisibilityOff()

    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(colors.GetColor3d('MistyRose'))

    renderer.AddActor(actor)

    render_window.Render()
    interactor.Start()


def vtk_version_ok(major, minor, build):
    """
    Check the VTK version.

    :param major: Major version.
    :param minor: Minor version.
    :param build: Build version.
    :return: True if the requested VTK version is greater or equal to the actual VTK version.
    """
    needed_version = 10000000000 * int(major) + 100000000 * int(minor) + int(build)
    try:
        vtk_version_number = VTK_VERSION_NUMBER
    except AttributeError:  # as error:
        ver = vtkVersion()
        vtk_version_number = 10000000000 * ver.GetVTKMajorVersion() + 100000000 * ver.GetVTKMinorVersion() \
                             + ver.GetVTKBuildVersion()
    if vtk_version_number >= needed_version:
        return True
    else:
        return False


if __name__ == '__main__':
    main()