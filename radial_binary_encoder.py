#!/usr/bin/env python3
import inkex
import math
import random
import time
from inkex import Circle, PathElement, TextElement, Group

class RadialBinaryEncoder(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--number", type=int, default=0, help="Input number")

    def effect(self):
        # Get user input
        number = self.options.number

        # Generate a random unique instance number (using timestamp + random)
        instance = int(time.time() * 1000) + random.randint(0, 999)
        
        # Default position: top-left corner (0, 0)
        # Note: Inkscape extensions don't directly access cursor position via CLI
        # For simplicity, we'll place it at (50, 50) to ensure visibility within padding
        center_x, center_y = 50, 50  # Adjusted from (0, 0) to avoid edge clipping

        # Create a group with a unique ID for this instance
        group = self.svg.add(Group())
        group.set('id', f'radial_binary_group_{instance}')

        # Step 1: Create a white disk with 1px black border, 67mm diameter
        radius = 33.5  # 67mm diameter -> 33.5mm radius
        disk = group.add(Circle.new(
            center=(center_x, center_y),
            radius=radius,
            style="fill:#ffffff;stroke:#000000;stroke-width:0.1px"
        ))

        # Step 2: Create a 24-degree sector (black) from edge to center
        self.create_sector(group, center_x, center_y, radius, 0, 24, "#000000")

        # Step 3: Process the number and create binary sectors
        # 3a: Convert number to 10-bit binary
        if number < 93:
            result = number + 606
        else:
            result = 1112 - number
        binary = format(result, '010b')  # 10-bit binary string

        # 3b: Create sectors for each bit
        for i, bit in enumerate(binary):
            start_angle = 24 + i * 24  # Start after the initial sector
            if bit == '0':
                self.create_sector(group, center_x, center_y, radius, start_angle, start_angle + 18, "#ffffff")
                self.create_sector(group, center_x, center_y, radius, start_angle + 18, start_angle + 24, "#000000")
            else:  # bit == '1'
                self.create_sector(group, center_x, center_y, radius, start_angle, start_angle + 6, "#ffffff")
                self.create_sector(group, center_x, center_y, radius, start_angle + 6, start_angle + 24, "#000000")

        # 3c: Add parity bit sector
        parity = binary.count('1') % 2  # 1 if odd, 0 if even
        start_angle = 24 + 10 * 24  # After the 10 bits
        if parity == 0:  # Even parity already, make it even with a 0 pattern
            self.create_sector(group, center_x, center_y, radius, start_angle, start_angle + 18, "#ffffff")
            self.create_sector(group, center_x, center_y, radius, start_angle + 18, start_angle + 24, "#000000")
        else:  # Odd, make it even with a 1 pattern
            self.create_sector(group, center_x, center_y, radius, start_angle, start_angle + 6, "#ffffff")
            self.create_sector(group, center_x, center_y, radius, start_angle + 6, start_angle + 24, "#000000")

        # Step 4: Create a white disk, 33mm diameter, no border
        group.add(Circle.new(
            center=(center_x, center_y),
            radius=16.5,  # 33mm diameter -> 16.5mm radius
            style="fill:#ffffff;stroke:none"
        ))

        # Step 5: Create a white equilateral triangle with 1px black border, 10mm sides
        side_length = 10  # 10mm
        height = (math.sqrt(3) / 2) * side_length  # Height of equilateral triangle
        x1 = center_x
        y1 = center_y - (height / 2)
        x2 = center_x - (side_length / 2)
        y2 = center_y + (height / 2)
        x3 = center_x + (side_length / 2)
        y3 = center_y + (height / 2)

        path_d = (
            f"M {x1},{y1} "
            f"L {x2},{y2} "
            f"L {x3},{y3} "
            f"Z"
        )
        
        group.add(PathElement(
            d=path_d,
            style="fill:#ffffff;stroke:#000000;stroke-width:0.1px"
        ))

        # Step 6: Add the user-provided number below the triangle
        text_y = center_y + 10
        text = group.add(TextElement())
        text.set('x', str(center_x))
        text.set('y', str(text_y))
        text.set('style', 'font-size:1mm;text-anchor:middle;fill:#000000;font-family:sans-serif')
        text.text = str(number)

    def create_sector(self, parent, cx, cy, radius, start_angle, end_angle, fill_color):
        """Create a sector path from start_angle to end_angle within the given parent element."""
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        x1 = cx + radius * math.cos(start_rad)
        y1 = cy + radius * math.sin(start_rad)
        x2 = cx + radius * math.cos(end_rad)
        y2 = cy + radius * math.sin(end_rad)
        
        large_arc = 1 if end_angle - start_angle > 180 else 0
        
        path_d = (
            f"M {cx},{cy} "
            f"L {x1},{y1} "
            f"A {radius},{radius} 0 {large_arc} 1 {x2},{y2} "
            f"Z"
        )
        
        parent.add(PathElement(
            d=path_d,
            style=f"fill:{fill_color};stroke:none"
        ))

if __name__ == '__main__':
    RadialBinaryEncoder().run()
