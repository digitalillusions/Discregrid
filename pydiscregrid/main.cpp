//
// Created by Stefan on 4/20/2020.
//

#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include <pybind11/functional.h>
#include <pybind11/stl.h>

#include <Discregrid/All>

namespace py = pybind11;
using namespace pybind11::literals;

PYBIND11_MODULE(pydiscregrid, m){

    py::class_<Discregrid::CubicLagrangeDiscreteGrid>(m, "CLDiscreteGrid")
            .def(py::init<const std::string>())
            .def(py::init<const Eigen::AlignedBox3d, std::array<unsigned int, 3>>())
            .def(py::init<>([](Eigen::Vector3d const& min, Eigen::Vector3d const& max, std::array<unsigned int, 3>const& res){
                Eigen::AlignedBox3d box(min, max);
                return Discregrid::CubicLagrangeDiscreteGrid(box, std::forward<std::array<unsigned int, 3>const&>(res));
            }))
            .def("save", &Discregrid::CubicLagrangeDiscreteGrid::save)
            .def("load", &Discregrid::CubicLagrangeDiscreteGrid::load)
            .def("addFunction", &Discregrid::CubicLagrangeDiscreteGrid::addFunction, "func"_a, "verbose"_a=false, py::arg_v("predicate", (Discregrid::DiscreteGrid::SamplePredicate*)nullptr, "Sample Predicate std::function<bool(Eigen::Vector3d const&)>"))
            .def("addSDF", [](Discregrid::CubicLagrangeDiscreteGrid & obj, const Discregrid::MeshDistance & md, bool verbose){
                auto func = Discregrid::DiscreteGrid::ContinuousFunction {};
                func = [&md](Eigen::Vector3d const& x){ return md.signedDistanceCached(x); };
                obj.addFunction(func, verbose);
            })
            .def("nCells", &Discregrid::CubicLagrangeDiscreteGrid::nCells)
            .def("determineShapeFunctions", &Discregrid::CubicLagrangeDiscreteGrid::determineShapeFunctions, "field_id"_a, "x"_a, "cell"_a, "c0"_a, "N"_a, "dN"_a=nullptr)
            .def("interpolate", (double (Discregrid::CubicLagrangeDiscreteGrid::*) (unsigned int, Eigen::Vector3d const &, const std::array<unsigned int, 32> &, const Eigen::Vector3d &, const Eigen::Matrix<double, 32, 1> &, Eigen::Vector3d *, Eigen::Matrix<double, 32, 3> *dN)const)(&Discregrid::CubicLagrangeDiscreteGrid::interpolate),
                    "field_id"_a, "xi"_a, "cell"_a, "c0"_a, "N"_a, "gradient"_a= nullptr, "dN"_a= nullptr)
            .def("interpolate", (double (Discregrid::CubicLagrangeDiscreteGrid::*)(unsigned int, Eigen::Vector3d const &, Eigen::Vector3d *)const)(&Discregrid::CubicLagrangeDiscreteGrid::interpolate),
                 "field_id"_a, "xi"_a, "gradient"_a=nullptr);

    py::class_<Discregrid::TriangleMesh>(m, "TriangleMesh")
            .def(py::init<std::vector<Eigen::Vector3d>const&, std::vector<std::array<unsigned int, 3>> const&>())
            .def(py::init<std::string const&>())
            .def("nFaces", &Discregrid::TriangleMesh::nFaces)
            .def("nVertices", &Discregrid::TriangleMesh::nVertices);

    py::class_<Discregrid::MeshDistance>(m, "MeshDistance")
            .def(py::init<Discregrid::TriangleMesh const&, bool>(), "mesh"_a, "precompute_normals"_a=true)
            .def("distance", &Discregrid::MeshDistance::distance, "x"_a, "nearestPoint"_a= nullptr, "nearestFace"_a= nullptr, "nearestEntity"_a= nullptr)
            .def("signedDistance", &Discregrid::MeshDistance::signedDistance, "x"_a)
            .def("signedDistance", [](const Discregrid::MeshDistance& obj, py::array_t<double> arr){
                auto r = arr.unchecked<2>();
                if (r.shape(1) != 3) throw std::domain_error("error: dim(1) != 3");
                const py::array_t<double> a = arr[py::make_tuple(py::ellipsis(), 0)].cast<py::array_t<double>>();
                const py::array_t<double> b = arr[py::make_tuple(py::ellipsis(), 1)].cast<py::array_t<double>>();
                const py::array_t<double> c = arr[py::make_tuple(py::ellipsis(), 2)].cast<py::array_t<double>>();
                return py::vectorize([obj](const double x, const double y, const double z){
                    const Eigen::Vector3d vec{x,y,z};
                    return obj.signedDistance(vec);
                })(a,b,c);
            })
            .def("signedDistanceNonVec", [](const Discregrid::MeshDistance& obj, py::array_t<double> arr){
                auto r = arr.unchecked<2>();
                if (r.shape(1) != 3) throw std::domain_error("error: dim(1) != 3");
                py::array_t<double> sdf_values = py::array(py::dtype("d"), {r.shape(0)}, {});
                auto s = sdf_values.mutable_unchecked<1>();
                for (int i = 0; i < r.shape(0); ++i) {
                    const Eigen::Vector3d vec{r(i, 0), r(i, 1), r(i, 2)};
                    s(i) = obj.signedDistance(vec);
                };
                return sdf_values;
            })
            .def("signedDistanceCached", &Discregrid::MeshDistance::signedDistance, "x"_a);
}
