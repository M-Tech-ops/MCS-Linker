cmake_minimum_required(VERSION 3.15)

# 1. FORCE the vcpkg toolchain and MinGW triplet
set(CMAKE_TOOLCHAIN_FILE "C:/Mc_autoset/FRESH/vcpkg/scripts/buildsystems/vcpkg.cmake" CACHE STRING "Vcpkg toolchain" FORCE)
set(VCPKG_TARGET_TRIPLET "x64-mingw-dynamic" CACHE STRING "Vcpkg triplet" FORCE)

# 2. Initialize the project
project(MinecraftDataTool)

# 3. FORCE C++20 Standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)
find
# 4. Find ZLIB
find_package(ZLIB REQUIRED)

# 5. Add executable
add_executable(main src/main.cpp)
add_executable(Comparator src/Comparator.cpp)
add_executable(Explorer src/NBT_Explorer_CLI.cpp)
target_include_directories(Explorer PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_include_directories(main PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_include_directories(Comparator PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
# 6. FLIP THE MASTER SWITCH ON! (This activates SimpleReadNbtFile)
target_compile_definitions(main PUBLIC CJF2_NBT_CPP_USE_ZLIB)
target_compile_definitions(Explorer PUBLIC CJF2_NBT_CPP_USE_ZLIB)
target_compile_definitions(Comparator PUBLIC CJF2_NBT_CPP_USE_ZLIB)
# 7. Link ZLIB
target_link_libraries(main PRIVATE ZLIB::ZLIB)
target_link_libraries(Explorer PRIVATE ZLIB::ZLIB)
target_link_libraries(Comparator PRIVATE ZLIB::ZLIB)