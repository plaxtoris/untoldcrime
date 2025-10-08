# C++ Game Development with MinGW Cross-Compiler
FROM debian:bookworm-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm

# Set working directory
WORKDIR /app

# Install build essentials and MinGW for Windows cross-compilation
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    make \
    g++ \
    mingw-w64 \
    git \
    pkg-config \
    htop \
    openssh-client \
    ca-certificates \
    wget \
    unzip \
    # OpenGL/Graphics libraries
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    # GLFW dependencies for native Linux builds (optional)
    libglfw3-dev \
    libglm-dev && \
    rm -rf /var/lib/apt/lists/*

# Download and build GLFW for Windows (MinGW)
RUN mkdir -p /tmp/glfw-build && cd /tmp/glfw-build && \
    wget https://github.com/glfw/glfw/releases/download/3.4/glfw-3.4.zip && \
    unzip glfw-3.4.zip && \
    cd glfw-3.4 && \
    mkdir build-mingw && cd build-mingw && \
    cmake .. \
        -DCMAKE_TOOLCHAIN_FILE=/app/toolchain-mingw.cmake \
        -DCMAKE_INSTALL_PREFIX=/usr/x86_64-w64-mingw32 \
        -DGLFW_BUILD_EXAMPLES=OFF \
        -DGLFW_BUILD_TESTS=OFF \
        -DGLFW_BUILD_DOCS=OFF \
        -DBUILD_SHARED_LIBS=OFF && \
    make -j$(nproc) && \
    make install && \
    cd / && rm -rf /tmp/glfw-build

# Download GLM (header-only library)
RUN mkdir -p /tmp/glm && cd /tmp/glm && \
    wget https://github.com/g-truc/glm/releases/download/0.9.9.8/glm-0.9.9.8.zip && \
    unzip glm-0.9.9.8.zip && \
    cp -r glm/glm /usr/x86_64-w64-mingw32/include/ && \
    cd / && rm -rf /tmp/glm

# Create MinGW CMake toolchain file
RUN echo 'set(CMAKE_SYSTEM_NAME Windows)\n\
set(CMAKE_C_COMPILER x86_64-w64-mingw32-gcc)\n\
set(CMAKE_CXX_COMPILER x86_64-w64-mingw32-g++)\n\
set(CMAKE_RC_COMPILER x86_64-w64-mingw32-windres)\n\
set(CMAKE_FIND_ROOT_PATH /usr/x86_64-w64-mingw32)\n\
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)\n\
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)\n\
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)' > /app/toolchain-mingw.cmake

# Create directory structure
RUN mkdir -p /app/src /app/build

CMD ["/bin/bash"]
