import tkinter as tk
from tkinter import messagebox
import math

class PhysicsEngine:
    def __init__(self, mass_large, velocity_large):
        # --- The Setup ---
        # We're simulating two blocks. m2 is our "reference" block (1kg).
        # m1 is the massive block that will crush m2 against the wall.
        self.m1 = mass_large       
        self.m2 = 1.0              
        
        # Where everyone starts on the screen
        self.x1 = 400.0            # Large block starts a bit to the right
        self.x2 = 200.0            # Small block is in the middle
        self.w1 = 150.0            # Large block width (visual only)
        self.w2 = 50.0             # Small block width (visual only)
        
        # Initial speeds
        self.v1 = velocity_large   # The large block comes barreling in (usually negative velocity)
        self.v2 = 0.0              # Small block is just sitting there waiting to get hit
        
        # We need to count how many times they hit to approximate Pi
        self.collisions = 0
        self.finished = False

    def step(self, dt):     
        # We track how much time we have left to simulate in this frame
        time_remaining = dt
        
        while time_remaining > 0:
            # 1. Check if the small block is about to smack into the wall (x=0)
            if self.v2 < 0:
                t_wall = self.x2 / abs(self.v2)
            else:
                # If it's moving away from the wall, it'll never hit it
                t_wall = float('inf')

            # 2. Check if the blocks are about to hit each other
            # Collision happens when the big block touches the right side of the small block
            if self.v1 < self.v2: 
                # We only care if the big block is actually catching up to the small one
                distance_between = self.x1 - (self.x2 + self.w2)
                closing_speed = self.v2 - self.v1
                t_block = distance_between / closing_speed
            else:
                t_block = float('inf')

            # Which happens first? The wall hit or the block hit?
            t_next = min(t_wall, t_block)

            if t_next <= time_remaining:
                # Okay, a collision happens *during* this time step.
                # Fast-forward exactly to the moment of impact.
                self.x1 += self.v1 * t_next
                self.x2 += self.v2 * t_next
                time_remaining -= t_next
                
                # Handle the bounce
                if t_wall < t_block:
                    self.resolve_wall_collision()
                else:
                    self.resolve_block_collision()
            else:
                # No collisions in this time step, just move everything forward normally
                self.x1 += self.v1 * time_remaining
                self.x2 += self.v2 * time_remaining
                time_remaining = 0
                
        # Check if we're done. 
        # This happens when both blocks are moving away from the wall (positive velocity)
        # AND the big block is moving faster than the small one, so they'll never touch again.
        if self.v1 >= 0 and self.v2 >= 0 and self.v1 >= self.v2:
            self.finished = True

    def resolve_wall_collision(self):
        # Bouncing off the wall just flips the direction
        self.v2 *= -1
        self.collisions += 1

    def resolve_block_collision(self):
        # Good old high school physics: 1D perfectly elastic collision formulas.
        # Conservation of momentum and kinetic energy.
        u1 = self.v1
        u2 = self.v2
        m1 = self.m1
        m2 = self.m2
        
        # The math gets messy, but this calculates the new velocities
        v1 = ((m1 - m2) * u1 + 2 * m2 * u2) / (m1 + m2)
        v2 = ((m2 - m1) * u2 + 2 * m1 * u1) / (m1 + m2)
        
        self.v1 = v1
        self.v2 = v2
        self.collisions += 1

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Colliding Blocks - Computing Pi")
        self.root.geometry("1000x600") 
        
        # --- UI Layout ---
        # Container for the drawing area
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Container for buttons and inputs at the bottom
        self.control_frame = tk.Frame(root, bg="#f0f0f0", pady=10)
        self.control_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # The actual drawing surface
        self.width = 1000
        self.height = 500
        self.canvas = tk.Canvas(self.canvas_frame, bg="#1e1e1e", width=self.width, height=self.height)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # --- Controls Section ---
        
        # Input for the Big Mass
        tk.Label(self.control_frame, text="Mass Large Block (kg):", bg="#f0f0f0", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
        self.mass_entry = tk.Entry(self.control_frame, font=("Arial", 12), width=10)
        self.mass_entry.insert(0, "100") # Start with 100kg so it doesn't take forever
        self.mass_entry.pack(side=tk.LEFT)

        # Input for Initial Speed
        tk.Label(self.control_frame, text="Initial Velocity (m/s):", bg="#f0f0f0", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
        self.vel_entry = tk.Entry(self.control_frame, font=("Arial", 12), width=8)
        self.vel_entry.insert(0, "-100.0")
        self.vel_entry.pack(side=tk.LEFT)

        # The "Go" Button
        self.reset_btn = tk.Button(self.control_frame, text="RESET / APPLY", command=self.reset_simulation, 
                                   bg="#3498db", fg="white", font=("Arial", 12, "bold"), padx=20)
        self.reset_btn.pack(side=tk.LEFT, padx=30)
        
        # Display the math prediction so we know if the code is working
        self.info_label = tk.Label(self.control_frame, text="Theoretical: 31", bg="#f0f0f0", fg="#555", font=("Arial", 12))
        self.info_label.pack(side=tk.RIGHT, padx=20)

        # Game State
        self.ground_y = 400
        self.engine = None
        
        # Kick things off
        self.reset_simulation()
        self.animate()

    def reset_simulation(self):
        try:
            # Grab user inputs
            m1 = float(self.mass_entry.get())
            v1 = float(self.vel_entry.get())
            
            if m1 <= 0:
                raise ValueError("Mass must be positive")
            
            # Spin up a fresh physics engine
            self.engine = PhysicsEngine(m1, v1)
            
            # Fun Fact: The number of collisions relates to Pi based on powers of 100 for the mass.
            # e.g., mass=100 -> 31 collisions (3.14...)
            theory = math.floor(math.pi * math.sqrt(m1))
            self.info_label.config(text=f"Theoretical Count: {theory}")
            
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values.")

    def draw(self):
        self.canvas.delete("all")
        
        if not self.engine: return

        # Draw the environment
        self.canvas.create_line(20, 50, 20, self.ground_y, fill="gray", width=5) # The Wall
        self.canvas.create_line(20, self.ground_y, self.width, self.ground_y, fill="gray", width=2) # The Floor
        
        # Draw Small Block (1kg)
        x2_draw = 20 + self.engine.x2
        y2_draw = self.ground_y - self.engine.w2
        self.canvas.create_rectangle(x2_draw, y2_draw, x2_draw + self.engine.w2, self.ground_y, 
                                     fill="#3498db", outline="white", width=2)
        self.canvas.create_text(x2_draw + self.engine.w2/2, y2_draw + self.engine.w2/2, text="1kg", fill="white")

        # Draw Large Block
        x1_draw = 20 + self.engine.x1
        
        # Visual trickery:
        # If the mass is 1,000,000kg, we can't draw it to scale or it covers the whole screen.
        # So we cheat and use a log scale to make it look "heavy" without breaking the UI.
        size_scale = math.log10(self.engine.m1) * 20 if self.engine.m1 > 1 else 20
        size1 = max(80, min(250, 50 + size_scale)) 
        
        y1_draw = self.ground_y - size1
        
        self.canvas.create_rectangle(x1_draw, y1_draw, x1_draw + size1, self.ground_y, fill="#e74c3c", outline="white", width=2)

        # Label the big mass
        mass_txt = f"{self.engine.m1:.0f} kg"
        self.canvas.create_text(x1_draw + size1/2, y1_draw + size1/2, text=mass_txt, fill="white", font=("Arial", 12, "bold"))

        # The big collision counter in the background
        self.canvas.create_text(self.width/2, 80, text=f"{self.engine.collisions}", fill="white", font=("Arial", 60, "bold"))
        
        if self.engine.finished:
             self.canvas.create_text(self.width/2, 160, text="FINISHED", fill="#2ecc71", font=("Arial", 20))

    def animate(self):
        if self.engine:
            dt = (1/60.0) 
            self.engine.step(dt)

        self.draw()
        self.root.after(16, self.animate)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()