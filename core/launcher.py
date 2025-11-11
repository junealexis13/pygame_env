import pygame
import random
import math
import sys
import tomllib, os

from .ball import Ball

with open(os.path.join("core",'gameconfig.toml'), 'rb') as conf:
    GAME_CONFIGS = tomllib.load(conf)
    VIEW = GAME_CONFIGS['view_parameters']
    COLORS = GAME_CONFIGS['colormaps']
    BALLPHYSICS = GAME_CONFIGS['ball_physics']


SCREEN_WIDTH = VIEW['SCREEN_WIDTH']
SCREEN_HEIGHT = VIEW['SCREEN_HEIGHT']
PEG_RADIUS = VIEW['PEG_RADIUS']
FPS = VIEW['FPS']

class PinballLauncher:
    def __init__(self, x, y, ball_rng=None):
        self.x = x
        self.y = y
        self.power = 0.0
        self.max_power = 20.0
        self.charging = False
        self.width = 30
        self.height = 120
        self.ball_rng = ball_rng
        
    def update(self, charging):
        self.charging = charging
        if charging:
            self.power = min(self.max_power, self.power + 0.2)
        else:
            # when not charging we don't reset power here; reset happens on launch
            pass

    def launch(self):
        if self.power <= 0:
            return None, 0

        # Calculate the velocity based on power
        velocity_magnitude = (self.power / self.max_power) * 15 
        vx = 0.0  # Horizontal velocity (can be adjusted if needed)
        vy = -velocity_magnitude  # Vertical velocity (upward)

        # Create the ball with the calculated velocities
        ball = Ball(self.x, self.y - 30, vx, vy, follow_ramp=True)
        ball.launch_speed = self.power / self.max_power  
        ball.vy = vy  

        # Set starting ramp position for the ball
        ball.start_ramp_x = self.x
        ball.start_ramp_y = self.y - 80

        launched_power = self.power
        self.power = 0.0  
        return ball, launched_power

    def draw(self, screen):
        # Draw outer tube body
        pygame.draw.rect(screen, COLORS['GRAY'], (self.x - 15, self.y - 60, 30, 120))
        pygame.draw.rect(screen, COLORS['WHITE'], (self.x - 15, self.y - 60, 30, 120), 3)
        # inner tube
        pygame.draw.rect(screen, COLORS['BLACK'], (self.x - 10, self.y - 55, 20, 110))

        # power indicator
        if self.charging:
            power_height = int((self.power / self.max_power) * 100)
            color = COLORS['GREEN'] if self.power < self.max_power * 0.7 else COLORS['YELLOW'] if self.power < self.max_power * 0.9 else COLORS['RED']
            pygame.draw.rect(screen, color, (self.x - 8, self.y + 50 - power_height, 16, power_height))

        # --- NEW TUBE PATH ---
        start_x = self.x
        start_y = self.y - 60
        straight_height = 150  # vertical section length
        straight_end_x = start_x
        straight_end_y = start_y - straight_height

        # draw straight vertical section
        pygame.draw.line(screen, COLORS['WHITE'], (start_x - 5, start_y), (straight_end_x - 5, straight_end_y), 3)
        pygame.draw.line(screen, COLORS['WHITE'], (start_x + 5, start_y), (straight_end_x + 5, straight_end_y), 3)
        pygame.draw.line(screen, COLORS['SILVER'], (start_x, start_y), (straight_end_x, straight_end_y), 2)

        # curve to top-middle peg (inverted U using quadratic Bezier)
        end_x = SCREEN_WIDTH // 2
        end_y = 100
        control_x = (straight_end_x + end_x) / 2
        control_y = straight_end_y - 90  # peak height of U

        ramp_points = []
        for i in range(20):
            t = i / 19.0
            rx = (1 - t)**2 * straight_end_x + 2 * (1 - t) * t * control_x + t**2 * end_x
            ry = (1 - t)**2 * straight_end_y + 2 * (1 - t) * t * control_y + t**2 * end_y
            ramp_points.append((int(rx), int(ry)))

        for i in range(len(ramp_points) - 1):
            pygame.draw.line(screen, COLORS['WHITE'],
                            (ramp_points[i][0] - 5, ramp_points[i][1] - 4),
                            (ramp_points[i+1][0] - 5, ramp_points[i+1][1] - 5), 3)
            pygame.draw.line(screen, COLORS['WHITE'],
                            (ramp_points[i][0] + 5, ramp_points[i][1] + 5),
                            (ramp_points[i+1][0] + 5, ramp_points[i+1][1] + 5), 3)
            pygame.draw.line(screen, COLORS['SILVER'], ramp_points[i], ramp_points[i+1], 2)


    def launch(self):
        if self.power <= 0:
            return None, 0

        velocity_magnitude = (self.power / self.max_power) * 10  # max speed scale
        vx = 0.0
        vy = -velocity_magnitude
        ball = Ball(self.x, self.y - 30, vx, vy, follow_ramp=True)
        ball.launch_speed = self.power / self.max_power
        ball.vy = -velocity_magnitude  # upward climb in tube

        # set starting ramp position for the ball
        ball.start_ramp_x = self.x
        ball.start_ramp_y = self.y - 60

        launched_power = self.power
        self.power = 0.0
        return ball, launched_power
