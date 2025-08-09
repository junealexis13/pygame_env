import pygame
import math

# Tube path: straight up, then gentle curve to center
def generate_tube_path(start_x, start_y, curve_height=200, curve_offset=150, steps=50):
    points = []
    for i in range(steps + 1):
        t = i / steps
        # Interpolate: first part vertical, then curve inward
        x = start_x + curve_offset * (t ** 2)  # slow start inward
        y = start_y - t * curve_height
        points.append((x, y))
    return points

class Tube:
    def __init__(self, x, y):
        self.path = generate_tube_path(x, y)
        self.width = 30
        self.inner_width = 20

    def draw(self, screen):
        # Draw outer tube
        pygame.draw.lines(screen, (128,128,128), False, self.path, self.width)
        pygame.draw.lines(screen, (255,255,255), False, self.path, 3)
        # Draw inner (hollow) part
        pygame.draw.lines(screen, (0,0,0), False, self.path, self.inner_width)

class Ball:
    def __init__(self, tube):
        self.tube = tube
        self.tube_index = 0
        self.in_tube = True
        self.x, self.y = tube.path[0]
        self.vx = 0
        self.vy = 0

    def update(self):
        if self.in_tube:
            self.tube_index += 1
            if self.tube_index >= len(self.tube.path):
                self.in_tube = False
                # launch velocity after tube exit
                self.vx = 0
                self.vy = -5
            else:
                self.x, self.y = self.tube.path[self.tube_index]
        else:
            # Normal gravity physics
            self.vy += 0.2
            self.x += self.vx
            self.y += self.vy

    def draw(self, screen):
        pygame.draw.circle(screen, (255,0,0), (int(self.x), int(self.y)), 8)

pygame.init()
screen = pygame.display.set_mode((600, 600))
clock = pygame.time.Clock()

tube = Tube(100, 500)
ball = Ball(tube)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    ball.update()

    screen.fill((50,50,50))
    tube.draw(screen)
    ball.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
