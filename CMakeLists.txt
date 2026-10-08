cmake_minimum_required(VERSION 3.10 FATAL_ERROR)

project(AsBotApi VERSION 10.3 LANGUAGES CXX)

add_subdirectory(adlib EXCLUDE_FROM_ALL)

if (NOT DEFINED CMAKE_MODULE_PATH)
  set(CMAKE_MODULE_PATH "")
endif()
set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/adlib/CMake" "${CMAKE_MODULE_PATH}")

if (NOT DEFINED CMAKE_INSTALL_BINDIR)
  set(CMAKE_INSTALL_BINDIR "bin")
endif()

if (POLICY CMP0074)
  # use environment variables to find libraries
  cmake_policy(SET CMP0074 NEW)
endif()

include(PreventInSourceBuild)
prevent_in_source_build()

if (AS_BOT_API_ENABLE_LTO)
  include(CheckIPOSupported)
  check_ipo_supported(RESULT IPO_SUPPORTED LANGUAGES CXX)
  if (IPO_SUPPORTED)
    string(REPLACE ";" " " CXX_FLAGS_IPO "${CMAKE_CXX_COMPILE_OPTIONS_IPO}")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${CXX_FLAGS_IPO}")

    string(REPLACE ";" " " LINK_FLAGS_IPO "${CMAKE_CXX_LINK_OPTIONS_IPO}")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${LINK_FLAGS_IPO}")
  endif()
endif()

set(CMAKE_THREAD_PREFER_PTHREAD ON)
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

if (THREADS_HAVE_PTHREAD_ARG)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -pthread")
endif()

include(TdSetUpCompiler)
td_set_up_compiler()

if (CLANG OR GCC)
  if (MEMPROF)
    include(CheckCXXCompilerFlag)
    check_cxx_compiler_flag(-no-pie CXX_NO_PIE_FLAG)
    if (CXX_NO_PIE_FLAG)
      set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -no-pie")
    elseif (APPLE)
      set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,-no_pie")
    endif()
    include(AddCXXCompilerFlag)
    add_cxx_compiler_flag("-static-libstdc++")
    add_cxx_compiler_flag("-static-libgcc")
  endif()
endif()

set(AS_BOT_API_SOURCE
  as-bot-api/telegram-bot-api.cpp

  as-bot-api/Client.cpp
  as-bot-api/ClientManager.cpp
  as-bot-api/HttpConnection.cpp
  as-bot-api/HttpStatConnection.cpp
  as-bot-api/Query.cpp
  as-bot-api/Stats.cpp
  as-bot-api/Watchdog.cpp
  as-bot-api/WebhookActor.cpp

  as-bot-api/Client.h
  as-bot-api/ClientManager.h
  as-bot-api/ClientParameters.h
  as-bot-api/HttpConnection.h
  as-bot-api/HttpServer.h
  as-bot-api/HttpStatConnection.h
  as-bot-api/Query.h
  as-bot-api/Stats.h
  as-bot-api/Watchdog.h
  as-bot-api/WebhookActor.h
)

add_executable(as-bot-api ${AS_BOT_API_SOURCE})
target_include_directories(as-bot-api PRIVATE $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>)
target_link_libraries(as-bot-api PRIVATE memprof tdactor tdcore tddb tdnet tdutils)

install(TARGETS as-bot-api RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}")
if (MSVC AND VCPKG_TOOLCHAIN)
  install(DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/$<CONFIG>/" DESTINATION "${CMAKE_INSTALL_BINDIR}" FILES_MATCHING PATTERN "*.dll" PATTERN "*.pdb")
endif()
