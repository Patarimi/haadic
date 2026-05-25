"""
A Python framework for analog IC design automation.

# Haadic structure:

 - core
    - flow: for defining and running design flows
    - steps: for defining the core steps in the design flow, such as layout generation, extraction, simulation, etc.
    - techno: for handling technology-specific information and operations.
 - io
    - readers: files readers (spice, raw, etc.)
    - writers: files writers (spice)
    - wrappers: for external tools (e.g., magic, netgen, etc.)
 - design
    - layouts: for layout generation and manipulation
    - models: for device and circuit modeling
    - evaluators: for performance evaluation
    - components: parameterized components (e.g., common sources) and design helpers (e.g., EKV model).
"""

name = "haadic"
