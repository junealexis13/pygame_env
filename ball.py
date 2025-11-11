import pygame
import random
import math
import sys
import tomllib, os

with open('gameconfig.toml', 'rb') as conf:
    GAME_CONFIGS = tomllib.load(conf)
    VIEW = GAME_CONFIGS['view_parameters']
    COLORS = GAME_CONFIGS['colormaps']
    BALLPHYSICS = GAME_CONFIGS['ball_physics']


SCREEN_WIDTH = VIEW['SCREEN_WIDTH']
SCREEN_HEIGHT = VIEW['SCREEN_HEIGHT']
PEG_RADIUS = VIEW['PEG_RADIUS']
FPS = VIEW['FPS']

class Ball:
    def __init__(self, x, y, vx=0, vy=0, follow_ramp=False, rng=None):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = PEG_RADIUS
        
        # Use passed RNG for reproducibility
        self.rng = rng if rng is not None else random.Random()
        self.color = self.rng.choice([COLORS['RED'], COLORS['BLUE'], COLORS['GREEN'], 
                                      COLORS['YELLOW'], COLORS['ORANGE'], COLORS['PURPLE']])
        
        self.gravity = BALLPHYSICS['gravity']
        self.bounce = BALLPHYSICS['bounce']
        self.friction = BALLPHYSICS['friction']
        self.active = True
        self.ramp_t = 0.0

        # For ramp behavior
        self.follow_ramp = follow_ramp
        self.ramp_progress = 0.0

    def update(self, pegs):
        if not self.active:
            return

        # If following ramp, move along straight + inverted U-curve to top-middle
        if self.follow_ramp:
            start_x = self.start_ramp_x
            start_y = self.start_ramp_y
            straight_height = 150
            straight_end_x = start_x
            straight_end_y = start_y - straight_height

            end_x = SCREEN_WIDTH // 2
            end_y = 100
            control_x = (straight_end_x + end_x) / 2
            control_y = straight_end_y - 100

            # If still in the vertical section
            if self.y > straight_end_y:
                self.y += self.vy
                self.vy += 0.2  # gravity slows climb

                if self.vy >= 0:  # didn't make it
                    self.follow_ramp = False
                    self.active = False  # mark as failed
                    return

            if self.ramp_t >= 1.0:
                self.follow_ramp = False
                # Set initial velocity based on launch power when transitioning to peg field
                self.vx = self.rng.uniform(-0.3, 0.3)
                self.vy = self.launch_speed * 12
            else:
                # FIXED: Use constant curve speed regardless of launch power
                if not hasattr(self, "curve_t"):
                    self.curve_t = 0.0
                self.curve_t += 0.05  # Fixed increment for reproducibility
                
                if self.curve_t >= 1.0:
                    self.follow_ramp = False
                    # FIXED: Predetermined exit velocity for reproducibility
                    # Use RNG but don't scale by launch_speed
                    self.vx = self.rng.uniform(-0.3, 0.3)
                    self.vy = 2.5  # Fixed vertical velocity
                    return
                    
                bx = (1 - self.curve_t)**2 * straight_end_x + 2 * (1 - self.curve_t) * self.curve_t * control_x + self.curve_t**2 * end_x
                by = (1 - self.curve_t)**2 * straight_end_y + 2 * (1 - self.curve_t) * self.curve_t * control_y + self.curve_t**2 * end_y
                self.x = bx
                self.y = by
            return

        # Normal physics
        self.vy += self.gravity
        self.vx *= self.friction
        self.x += self.vx
        self.y += self.vy

        self.vx *= 0.99
        self.vy *= 0.99

        # Screen side collisions
        # Rail collisions
        top_y = 150
        bottom_y = SCREEN_HEIGHT - 80
        rail_offset_x = 200

        # Left rail slope equation
        if self.y >= top_y and self.y <= bottom_y:
            left_x_at_y = (SCREEN_WIDTH//2 - rail_offset_x) - ((SCREEN_WIDTH//2 - rail_offset_x) / (bottom_y - top_y)) * (self.y - top_y)
            right_x_at_y = (SCREEN_WIDTH//2 + rail_offset_x) + ((SCREEN_WIDTH - (SCREEN_WIDTH//2 + rail_offset_x)) / (bottom_y - top_y)) * (self.y - top_y)

            if self.x - self.radius < left_x_at_y:
                self.x = left_x_at_y + self.radius
                self.vx = -self.vx * self.bounce

            if self.x + self.radius > right_x_at_y:
                self.x = right_x_at_y - self.radius
                self.vx = -self.vx * self.bounce

        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = -self.vx * self.bounce
        if self.x + self.radius > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vx = -self.vx * self.bounce

        # Collision with pegs
        for peg in pegs:
            dx = self.x - peg[0]
            dy = self.y - peg[1]
            dist = math.hypot(dx, dy)
            if dist == 0:
                continue
            if dist < self.radius + PEG_RADIUS:
                # Normalize
                nx = dx / dist
                ny = dy / dist
                overlap = self.radius + PEG_RADIUS - dist
                # Separate
                self.x += nx * overlap
                self.y += ny * overlap
                # Reflect velocity
                dot = self.vx * nx + self.vy * ny
                self.vx -= 2 * dot * nx
                self.vy -= 2 * dot * ny
                # damping & randomness - FIXED: Don't scale by launch_speed
                self.vx *= 0.9
                self.vy *= self.bounce
                self.vx += self.rng.uniform(-0.3, 0.3)

    def draw(self, screen):
        if not self.active:
            return
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        # simple highlight
        pygame.draw.circle(screen, COLORS['WHITE'], (int(self.x - 2), int(self.y - 2)), 3)