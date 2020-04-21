import pydiscregrid
import numpy as np
import meshio


def main():
    print("Loading mesh...")
    mesh = meshio.read("C:/Users/Stefan/Downloads/treefrog_45_cut.stl")
    tri_mesh = pydiscregrid.TriangleMesh(mesh.points, mesh.cells[0].data)
    print(f"\tFound {tri_mesh.nVertices()} vertices and {tri_mesh.nFaces()} faces.")
    print("\tDone.")

    print("Set up data structures...")
    md = pydiscregrid.MeshDistance(tri_mesh)
    print("\tDone.")

    print("Computing bounding box...")
    max = np.max(mesh.points, axis=0)
    min = np.min(mesh.points, axis=0)
    print(f"\tMin {min}\n\tMax {max}")
    min -= 1e-3 * np.linalg.norm(max - min, ord=2) * np.ones_like(min)
    max += 1e-3 * np.linalg.norm(max - min, ord=2) * np.ones_like(max)
    print(f"\tMin {min}\n\tMax {max}")
    grid = pydiscregrid.CLDiscreteGrid(min, max, [20, 20, 20])
    print(f"\tConstructed {grid.nCells()} cells.")

    print(f"Generate Discretization...")
    grid.addSDF(md, True)
    print(f"\tDone.")


if __name__ == '__main__':
    main()