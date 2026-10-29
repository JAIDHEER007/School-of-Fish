![Animation](https://64.media.tumblr.com/fdc3473a266d23c9e8457278662cb584/cd5aec85d91b4e9e-29/s500x750/0dc6ac5170aa96a8141a007d30d38c437a064813.gif)

# School of Fish

A fish schooling (boids) n-body simulation in C++ with real-time 2D and 3D visualization.

This is a learning project. The goal is to go step by step from a simple brute-force
O(n²) implementation to algorithmic optimization (a spatial grid), then multi-core
(OpenMP), and finally the GPU (CUDA), and to measure the speedup at each step.

**Current phase:** Phase 1, not started

---

## Tech stack

| Purpose            | Choice                                              |
|--------------------|-----------------------------------------------------|
| Language           | C++20                                               |
| Build              | CMake 3.24+, all dependencies fetched with `FetchContent` |
| Window / input     | [GLFW](https://www.glfw.org/)                       |
| OpenGL loader      | [glad](https://github.com/Dav1dde/glad) (OpenGL 4.3 core) |
| Debug UI           | [Dear ImGui](https://github.com/ocornut/imgui) (GLFW + OpenGL3 backends) |
| Math               | [glm](https://github.com/g-truc/glm)                |
| Multi-core (later) | OpenMP, optional (`FISH_ENABLE_OPENMP`)             |
| GPU (later)        | CUDA, optional (`FISH_ENABLE_CUDA`)                 |

The project should build with **one configure and one build command**, with no manual
library installs. OpenMP and CUDA are off by default, so a CPU-only build always works.

---

## Architecture rules

These apply from the very first line of code:

1. **Structure of Arrays, always 3D.** Simulation data is stored as separate arrays
   `x, y, z, vx, vy, vz`. 2D mode means `z` is fixed at 0 and z forces are zeroed.
   The simulation has no separate 2D and 3D code paths.
2. **One backend interface.** Every simulation backend implements the same interface:
   ```cpp
   class SimBackend {
       virtual void init(int n, const SimParams& params, uint32_t seed) = 0;
       virtual void step() = 0;
       // + read access to positions and velocities
   };
   ```
   Planned backends: `NaiveCPU`, `GridCPU`, OpenMP variants of both, `NaiveCUDA`,
   `TiledCUDA`, `GridCUDA`.
3. **Renderer is separate from the simulation.** It only reads position/velocity buffers.
   All fish are drawn with **one instanced draw call** (per-instance position + velocity),
   and the vertex shader turns each fish to face along its velocity.
4. **Fixed simulation timestep**, decoupled from the render frame rate.

### Planned layout

```
src/app/        main(), window, main loop, ImGui panels, command-line parsing
src/render/     shaders, buffers, instanced fish renderer, camera
src/sim/        SimBackend interface + CPU backends (naive, grid, OpenMP)
src/sim/cuda/   CUDA backends (.cu files)
shaders/        GLSL files, copied next to the binary at build time
bench/          benchmark scripts and recorded results
docs/           notes per phase, profiling write-ups
```

---

## Roadmap

Tick phases off as they are finished. Don't start a phase before the previous one works.

- [ ] Phase 1: Skeleton, window, instanced rendering test
- [ ] Phase 2: 2D brute-force boids
- [ ] Phase 2.1: Obstacles, walls, predators
- [ ] Phase 3: 3D rendering
- [ ] Phase 4: Uniform grid
- [ ] Phase 5: OpenMP
- [ ] Phase 6: CUDA (6a–6e)
- [ ] Phase 7: Packaging

### Phase 1: Skeleton, window, instanced rendering test
- CMake project; GLFW, glad, ImGui and glm fetched with FetchContent
- Window with an OpenGL 4.3 core context, ImGui overlay showing FPS and frame time
- Instanced rendering test: ~10,000 small triangles at random positions, each pointed
  along a random velocity, drifting slowly and wrapping at the screen edges (a simple
  CPU update is enough)
- ImGui slider for the instance count, plus a pause button
- Shaders loaded from `shaders/` (copied next to the binary at build time)
- `.gitignore`, first commit

*What you learn:* CMake + FetchContent, OpenGL context creation, VAO/VBO layout,
instancing (`glVertexAttribDivisor`, `glDrawArraysInstanced`), shader compile/link,
the ImGui frame loop.

### Phase 2: 2D brute-force boids, O(n²)
- Separation, alignment, cohesion, plus a small random wander
- Random initial positions and velocities with a **fixed seed**
- ImGui sliders for weights, radii and fish count
- Headless benchmark mode: `--bench --n N --steps S` prints ms/step

*What you learn:* the boids rules, the `SimBackend` interface, fixed-timestep loops,
measuring performance honestly (warm-up, averaging, release builds).

### Phase 2.1: Obstacles, walls, predators
- Circle/sphere obstacles that fish steer around
- World walls (soft steering away from the boundary)
- Hunter fish that chase, and fish that flee from them

*What you learn:* composing steering behaviors, keeping the SoA layout when adding
new kinds of agents.

### Phase 3: 3D rendering
- Perspective orbit camera
- 3D fish mesh, depth testing, simple lighting
- 2D / 3D toggle (the simulation stays the same, only z is freed)

*What you learn:* view/projection matrices, building an orientation from a velocity
vector, normals and basic lighting, the depth buffer.

### Phase 4: Uniform grid spatial partitioning
- Bin fish into grid cells; sort by cell index with a **counting sort**
- Each fish only checks neighboring cells instead of every other fish

*What you learn:* turning O(n²) into roughly O(n), counting sort / prefix sums,
cache locality, choosing a cell size relative to the interaction radius.

### Phase 5: OpenMP
- Parallelize the brute-force and grid backends
- Parallel grid build (counting, prefix sum, scatter)
- Benchmark threads vs. speedup

*What you learn:* `#pragma omp parallel for`, data races, scheduling, false sharing,
Amdahl's law.

### Phase 6: CUDA
- [ ] **6a** Naive O(n²) kernel
- [ ] **6b** Shared-memory tiling
- [ ] **6c** Grid backend using `thrust::sort_by_key`
- [ ] **6d** CUDA-OpenGL interop (the simulation writes straight into the render buffer)
- [ ] **6e** Nsight profiling notes in `docs/`

*What you learn:* the thread/block/grid model, memory coalescing, shared memory,
GPU sorting, avoiding CPU↔GPU copies, reading a profiler.

### Phase 7: Packaging
- GitHub Actions builds for Windows and Linux
- Static linking
- Release zips

*What you learn:* CI, cross-platform CMake, shipping a binary that runs on other machines.

---

## Build & run (planned)

These commands will work once Phase 1 is done (`--bench` once Phase 2 is done):

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j

./build/school_of_fish                          # interactive window
./build/school_of_fish --bench --n 10000 --steps 500   # headless benchmark
```

Optional backends (later phases):

```bash
cmake -S . -B build -DFISH_ENABLE_OPENMP=ON -DFISH_ENABLE_CUDA=ON
```

### Prerequisites (Ubuntu)

FetchContent downloads the libraries, but GLFW still needs the system window-system
headers to compile on Linux:

```bash
sudo apt install build-essential cmake ninja-build pkg-config \
    libx11-dev libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev \
    libxkbcommon-dev libwayland-dev wayland-protocols libgl-dev
```

glad 2 generates its loader with Python, so you also need Python 3 with the `jinja2`
package (`sudo apt install python3-jinja2`).

### Hardware note

The development machine has an Intel Iris Xe GPU (OpenGL 4.6), which is fine for
Phases 1–5. It has **no NVIDIA GPU**, so Phase 6 (CUDA) needs an NVIDIA machine or a
cloud GPU instance.
