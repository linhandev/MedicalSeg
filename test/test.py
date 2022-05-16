# from numpy import pi, sin, cos, mgrid
# dphi, dtheta = pi/250.0, pi/250.0
# [phi,theta] = mgrid[0:pi+dphi*1.5:dphi,0:2*pi+dtheta*1.5:dtheta]
# m0 = 4; m1 = 3; m2 = 2; m3 = 3; m4 = 6; m5 = 2; m6 = 6; m7 = 4;
# r = sin(m0*phi)**m1 + cos(m2*phi)**m3 + sin(m4*theta)**m5 + cos(m6*theta)**m7
# x = r*sin(phi)*cos(theta)
# y = r*cos(phi)
# z = r*sin(phi)*sin(theta)

# print(x.shape)
# print(x)
# # View it.
# from mayavi import mlab
# s = mlab.mesh(x, y, z)
# mlab.show()

# s = mlab.mesh(x, y, z)
# mlab.show()


# import pylab
# from numpy import pi, sin, cos, mgrid
# from mpl_toolkits.mplot3d import Axes3D
# import numpy as np 

# x= np.arange(-1,1,0.1)
# y= np.arange(-1,1,0.1) 
# x, y= np.meshgrid(x, y)
# z = np.cos(x* np.pi/2)
# print(x.shape, y.shape, z.shape)

# fig = pylab.figure()
# ax = Axes3D( fig )
# surf = ax.plot_surface(x, y, z, linewidth=0, antialiased=True )
# fig.canvas.set_window_title( "Distance" )
# pylab.show()


# import matplotlib.pyplot as plt
# import numpy as np


# # prepare some coordinates
# x, y, z = np.indices((8, 8, 8))

# # draw cuboids in the top left and bottom right corners, and a link between
# # them
# cube1 = (x < 3) & (y < 3) & (z < 3)
# cube2 = (x >= 5) & (y >= 5) & (z >= 5)
# link = abs(x - y) + abs(y - z) + abs(z - x) <= 2

# # combine the objects into a single boolean array
# voxelarray = cube1 | cube2 | link

# # set the colors of each object
# colors = np.empty(voxelarray.shape, dtype=object)
# colors[link] = 'red'
# colors[cube1] = 'blue'
# colors[cube2] = 'green'

# print(voxelarray.shape, voxelarray)
# # and plot everything
# ax = plt.figure().add_subplot(projection='3d')
# ax.voxels(voxelarray, facecolors=colors, edgecolor='k')

# plt.show()



import matplotlib.pyplot as plt
import numpy as np


n_radii = 8
n_angles = 36

# Make radii and angles spaces (radius r=0 omitted to eliminate duplication).
radii = np.linspace(0.125, 1.0, n_radii)
angles = np.linspace(0, 2*np.pi, n_angles, endpoint=False)[..., np.newaxis]

# Convert polar (radii, angles) coords to cartesian (x, y) coords.
# (0, 0) is manually added at this stage,  so there will be no duplicate
# points in the (x, y) plane.
x = np.append(0, (radii*np.cos(angles)).flatten())
y = np.append(0, (radii*np.sin(angles)).flatten())

# Compute z to make the pringle surface.
z = np.sin(-x*y)

print(x.shape, y.shape, z.shape)
ax = plt.figure().add_subplot(projection='3d')

ax.plot_trisurf(x, y, z, linewidth=0.2, antialiased=True)

plt.show()