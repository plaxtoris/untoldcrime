# Makefile for cross-compiling Windows .exe from Linux using MinGW

# Compiler and flags
CXX = x86_64-w64-mingw32-g++
CXXFLAGS = -std=c++17 -Wall -O2
INCLUDES = -I/usr/x86_64-w64-mingw32/include
LDFLAGS = -L/usr/x86_64-w64-mingw32/lib
LIBS = -lglfw3 -lopengl32 -lgdi32 -static-libgcc -static-libstdc++

# Directories
SRC_DIR = src
BUILD_DIR = build

# Target executable
TARGET = $(BUILD_DIR)/helloworld.exe

# Source files
SOURCES = $(SRC_DIR)/main.cpp

# Object files
OBJECTS = $(BUILD_DIR)/main.o

# Default target
all: $(TARGET)

# Create build directory if it doesn't exist
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Compile object files
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) -c $< -o $@

# Link executable
$(TARGET): $(OBJECTS)
	$(CXX) $(OBJECTS) $(LDFLAGS) $(LIBS) -o $(TARGET) -mwindows
	@echo ""
	@echo "==================================="
	@echo "Build successful!"
	@echo "Windows executable: $(TARGET)"
	@echo "==================================="

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)

# Rebuild everything
rebuild: clean all

# Run info (reminder that this is a Windows .exe)
info:
	@echo "This Makefile builds a Windows .exe using MinGW cross-compiler"
	@echo "To build: make"
	@echo "To clean: make clean"
	@echo "Output: $(TARGET)"
	@echo ""
	@echo "Note: The .exe must be run on Windows or with Wine on Linux"

.PHONY: all clean rebuild info
