#!/usr/bin/env python

import os
import sys

# noinspection PyUnresolvedReferences
import vtkmodules.vtkInteractionStyle

# noinspection PyUnresolvedReferences
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkCommonCore import VTK_VERSION_NUMBER, vtkVersion
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonDataModel import vtkDataObject, vtkDataSetAttributes
from vtkmodules.vtkFiltersCore import (
    vtkMaskFields,
    vtkThreshold,
    vtkWindowedSincPolyDataFilter,
    vtkSmoothPolyDataFilter,
)
from vtkmodules.vtkFiltersGeneral import vtkDiscreteFlyingEdges3D, vtkDiscreteMarchingCubes
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter
from vtkmodules.vtkIOImage import vtkNIFTIImageReader
from vtkmodules.vtkIOXML import vtkXMLPolyDataWriter
from vtkmodules.vtkImagingStatistics import vtkImageAccumulate
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkLight,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer,
)
from vtkmodules.vtkFiltersCore import vtkDecimatePro, vtkTriangleFilter
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkImagingGeneral import vtkImageGaussianSmooth
from vtkmodules.vtkFiltersCore import vtkStripper


def main():
    # vtkDiscreteFlyingEdges3D was introduced in VTK >= 8.2
    use_flying_edges = vtk_version_ok(8, 2, 0)

    # file_name, start_label, end_label = get_program_parameters()
    file_name, start_label, end_label = "/git/coronacases_001.nii.gz", 1, 2

    # Create all of the classes we will need

    smoother = vtkWindowedSincPolyDataFilter()
    selector = vtkThreshold()
    scalars_off = vtkMaskFields()
    geometry = vtkGeometryFilter()

    # Define all of the variables
    # smoothing_iterations = 20
    # pass_band = 0.001
    # feature_angle = 45
    # reduction = 0.90

    # Generate models from labels
    # 1) Read label file
    # 2) Generate a histogram of the labels
    # 3) Generate models from the labeled volume
    # 4) Smooth the models
    # 5) Output each model into a separate file

    tail = None

    # 1. reader
    reader = vtkNIFTIImageReader()
    reader.SetFileName(file_name)
    tail = reader.GetOutputPort()

    # 2. gaussian
    # maybe gauss only works with marching cubes
    # gauss = vtkImageGaussianSmooth()
    # gauss.SetInputConnection(tail)
    # tail = gauss.GetOutputPort()

    # gauss.SetStandardDeviation(0.8, 0.8, 0.8)
    # gauss.SetRadiusFactors(1.5, 1.5, 1.5)

    # 3. to mesh
    use_flying_edges = True
    if use_flying_edges:
        try:
            using_marching_cubes = False
            discrete_cubes = vtkDiscreteFlyingEdges3D()
        except AttributeError:
            using_marching_cubes = True
            discrete_cubes = vtkDiscreteMarchingCubes()
    else:
        using_marching_cubes = True
        discrete_cubes = vtkDiscreteMarchingCubes()

    discrete_cubes.SetInputConnection(tail)
    tail = discrete_cubes.GetOutputPort()

    discrete_cubes.GenerateValues(end_label - start_label + 1, start_label, end_label)
    discrete_cubes.Update()

    # 4.
    # transform = vtkTransform()
    # transformPD = vtkTransformPolyDataFilter()
    # transformPD.SetInputConnection(tail)
    # tail = transformPD.GetOutputPort()

    # transformPD.ReleaseDataFlagOn()
    # transformPD.SetTransform(transform)
    # transformPD.Update()

    # simplify mesh
    decimate = vtkDecimatePro()
    decimate.SetInputConnection(tail)
    tail = decimate.GetOutputPort()

    decimate.SetTargetReduction(0.70)
    # decimate.SetFeatureAngle(45)
    # decimate.SetMaximumError(0.002)
    # decimate.SetPreserveTopology(1)
    decimate.Update()

    # smooth the mesh
    # smoother = vtkWindowedSincPolyDataFilter()
    smoother = vtkSmoothPolyDataFilter()
    smoother.SetInputConnection(decimate.GetOutputPort())
    tail = smoother.GetOutputPort()

    smoother.SetNumberOfIterations(20)
    smoother.SetBoundarySmoothing(0)
    smoother.SetFeatureEdgeSmoothing(0)
    smoother.SetFeatureAngle(120)

    # smoother.SetRelaxationFactor(0.01)
    # smoother.SetConvergence(0)

    # smoother.SetPassBand(0.001)
    # smoother.NonManifoldSmoothingOn()
    # smoother.NormalizeCoordinatesOn()

    smoother.Update()

    # selector.SetInputConnection(smoother.GetOutputPort())
    # if use_flying_edges:
    #     if using_marching_cubes:
    #         selector.SetInputArrayToProcess(
    #             0, 0, 0, vtkDataObject().FIELD_ASSOCIATION_CELLS, vtkDataSetAttributes().SCALARS
    #         )
    #     else:
    #         selector.SetInputArrayToProcess(
    #             0, 0, 0, vtkDataObject().FIELD_ASSOCIATION_POINTS, vtkDataSetAttributes().SCALARS
    #         )
    # else:
    #     selector.SetInputArrayToProcess(
    #         0, 0, 0, vtkDataObject().FIELD_ASSOCIATION_CELLS, vtkDataSetAttributes().SCALARS
    #     )

    # Strip the scalars from the output
    scalars_off.SetInputConnection(tail)
    tail = scalars_off.GetOutputPort()
    scalars_off.CopyAttributeOff(vtkMaskFields().POINT_DATA, vtkDataSetAttributes().SCALARS)
    scalars_off.CopyAttributeOff(vtkMaskFields().CELL_DATA, vtkDataSetAttributes().SCALARS)

    geometry.SetInputConnection(scalars_off.GetOutputPort())
    tail = geometry.GetOutputPort()

    # selector.SetLowerThreshold(1)
    # selector.SetUpperThreshold(2)

    mapper = vtkPolyDataMapper()
    mapper.SetInputConnection(tail)
    mapper.SetScalarRange(start_label, end_label)
    mapper.SetScalarModeToUseCellData()
    mapper.SetColorModeToMapScalars()

    colors = vtkNamedColors()

    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(colors.GetColor3d("Green"))

    renderer = vtkRenderer()
    render_window = vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(1280, 960)
    render_window.SetWindowName("MedicalSeg Visulization Tool 3D")

    render_window_interactor = vtkRenderWindowInteractor()
    style = vtkInteractorStyleTrackballCamera()
    render_window_interactor.SetInteractorStyle(style)
    render_window_interactor.SetRenderWindow(render_window)
    


    renderer.AddActor(actor)
    renderer.SetBackground(colors.GetColor3d("Black"))
    renderer.SetAutomaticLightCreation(1)
    renderer.SetLightFollowCamera(1)
    renderer.SetAmbient(1, 1, 1)

    render_window.Render()

    camera = renderer.GetActiveCamera()
    camera.SetPosition(42.301174, 939.893457, -124.005030)
    camera.SetFocalPoint(224.697134, 221.301653, 146.823706)
    camera.SetViewUp(0.262286, -0.281321, -0.923073)
    camera.SetDistance(789.297581)
    camera.SetClippingRange(168.744328, 1509.660206)

    light = vtkLight()
    # light.SetPosition(camera.GetPosition())
    # light.PositionalOn()
    light.SetFocalPoint(actor.GetPosition())
    light.SetColor(colors.GetColor3d("White"))
    light.SetLightTypeToHeadlight()
    renderer.AddLight(light)

    print(renderer.GetLights())

    render_window_interactor.Start()


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
        vtk_version_number = (
            10000000000 * ver.GetVTKMajorVersion()
            + 100000000 * ver.GetVTKMinorVersion()
            + ver.GetVTKBuildVersion()
        )
    if vtk_version_number >= needed_version:
        return True
    else:
        return False


if __name__ == "__main__":
    main()
