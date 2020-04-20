add_subdirectory(pybind11)
pybind11_add_module(pydiscregrid main.cpp)
target_link_libraries(pydiscregrid PRIVATE Discregrid)
set_target_properties(pydiscregrid PROPERTIES DEBUG_POSTFIX "")