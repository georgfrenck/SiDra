# SiDra
Small program for  drawing  simplicial  complexes and computing  their homology. Short Demonstration is available at

[youtube.com/watch?v=JBbOWaeZRk4](https://youtu.be/JBbOWaeZRk4)

A precompiled version (for Mac OS X) can be found here:

[Frenck.net/Math/SiDra/SiDra.pkg](http://frenck.net/math/Sidra/Sidra.pkg)

## Draw simplicial complexes in the plane (2D-mode)
You can draw simplicial complexes by simply using your mouse in conjunction with the three buttons "0-simplices", "1-simplices" and "2-simplices" at the top. The button "eraser" activates the eraser mode and everything you now click on gets erased. By clicking the "erase all" button, everything is erased.

Simplices can als be added and removed in the lists on the left.

## Import and modify simplicial complexes
Using the "Data" button, you can import files from the folder "Data". There are a few sample data available.

Using this import, it is also possible to create simplicial complexes in 3D-space. 
For these, it is no longer possible to draw additional simplices or use the eraser mode as before.
In 3D-mode you can use the slider to change the perspective

## Check Orientability

In 3D-Mode you can also check if the simplicial complex is orientable in the sense that it has trivial normal bundle. 

For each 2-simplex, a normal vector is chosen in a way that the scalar products of normal vectors of adjacent 2-simplices is positive. If it is possible, the complex is orientable and we add a coloring to distinguish the two sides of the complex.

If it is not possible to coherently choose normal vectors, this does not exclude orientability since angles between adjacent 2-simplices might simply be too large.
