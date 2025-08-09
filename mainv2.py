import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60
PEG_RADIUS = 8

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 100, 100)
BLUE = (100, 150, 255)
GREEN = (100, 255, 100)
YELLOW = (255, 255, 100)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
PINK = (255, 192, 203)
CYAN = (0, 255, 255)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
GRAY = (128, 128, 128)

class Ball:
    def __init__(self, x, y, vx=0, vy=0, follow_ramp=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = 8
        self.color = random.choice([RED, BLUE, GREEN, YELLOW, ORANGE, PURPLE])
        self.gravity = 0.1
        self.bounce = 0.7
        self.friction = 0.995
        self.active = True

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

            else:
                # Now in curve section — use Bezier param based on climb velocity
                if not hasattr(self, "curve_t"):
                    self.curve_t = 0.0
                self.curve_t += max(0.01, self.launch_speed * 0.05)
                if self.curve_t >= 1.0:
                    self.follow_ramp = False
                    self.vx += random.uniform(-0.5, 0.5) * self.launch_speed
                    self.vy = 1.0 + 4.0 * self.launch_speed  # more charge → faster drop
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
                # damping & randomness
                self.vx *= 0.9
                self.vy *= self.bounce
                self.vx += random.uniform(-0.3, 0.3) * self.launch_speed


    def draw(self, screen):
        if not self.active:
            return
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        # simple highlight
        pygame.draw.circle(screen, WHITE, (int(self.x - 2), int(self.y - 2)), 3)

class PinballLauncher:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.power = 0.0
        self.max_power = 20.0
        self.charging = False
        self.width = 30
        self.height = 120

    def update(self, charging):
        self.charging = charging
        if charging:
            self.power = min(self.max_power, self.power + 0.2)
        else:
            # when not charging we don't reset power here; reset happens on launch
            pass

    def draw(self, screen):
        # Draw outer tube body
        pygame.draw.rect(screen, GRAY, (self.x - 15, self.y - 60, 30, 120))
        pygame.draw.rect(screen, WHITE, (self.x - 15, self.y - 60, 30, 120), 3)
        # inner tube
        pygame.draw.rect(screen, BLACK, (self.x - 10, self.y - 55, 20, 110))

        # power indicator
        if self.charging:
            power_height = int((self.power / self.max_power) * 100)
            color = GREEN if self.power < self.max_power * 0.7 else YELLOW if self.power < self.max_power * 0.9 else RED
            pygame.draw.rect(screen, color, (self.x - 8, self.y + 50 - power_height, 16, power_height))

        # --- NEW TUBE PATH ---
        start_x = self.x
        start_y = self.y - 60
        straight_height = 150  # vertical section length
        straight_end_x = start_x
        straight_end_y = start_y - straight_height

        # draw straight vertical section
        pygame.draw.line(screen, WHITE, (start_x - 5, start_y), (straight_end_x - 5, straight_end_y), 3)
        pygame.draw.line(screen, WHITE, (start_x + 5, start_y), (straight_end_x + 5, straight_end_y), 3)
        pygame.draw.line(screen, SILVER, (start_x, start_y), (straight_end_x, straight_end_y), 2)

        # curve to top-middle peg (inverted U using quadratic Bezier)
        end_x = SCREEN_WIDTH // 2
        end_y = 100
        control_x = (straight_end_x + end_x) / 2
        control_y = straight_end_y - 100  # peak height of U

        ramp_points = []
        for i in range(20):
            t = i / 19.0
            # Quadratic Bezier formula
            rx = (1 - t)**2 * straight_end_x + 2 * (1 - t) * t * control_x + t**2 * end_x
            ry = (1 - t)**2 * straight_end_y + 2 * (1 - t) * t * control_y + t**2 * end_y
            ramp_points.append((int(rx), int(ry)))

        # draw curve segment
        for i in range(len(ramp_points) - 1):
            pygame.draw.line(screen, WHITE,
                            (ramp_points[i][0] - 5, ramp_points[i][1] - 4),
                            (ramp_points[i+1][0] - 5, ramp_points[i+1][1] - 5), 3)
            pygame.draw.line(screen, WHITE,
                            (ramp_points[i][0] + 5, ramp_points[i][1] + 5),
                            (ramp_points[i+1][0] + 5, ramp_points[i+1][1] + 5), 3)
            pygame.draw.line(screen, SILVER, ramp_points[i], ramp_points[i+1], 2)


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

class Button:
    def __init__(self, x, y, width, height, text, color, text_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font = pygame.font.Font(None, 28)
        self.hovered = False

    def draw(self, screen):
        color = tuple(min(255, c + 20) for c in self.color) if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class PlinkoGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("DOST 3 Plinko Reward Game")
        self.clock = pygame.time.Clock()
        

        # Game states
        self.launched_once = False
        self.state = "splash"  # splash, playing, result
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.font_tiny = pygame.font.Font(None, 12)

        # Game objects
        self.balls = []
        self.pegs = self.create_pegs()
        self.reward_slots = self.create_reward_slots()
        self.launcher = PinballLauncher(80, SCREEN_HEIGHT // 2 + 60)
        self.back_button = Button(20, 20, 100, 40, "Back", BLUE, WHITE)

        # UI / result vars
        self.last_reward = None
        self.result_timer = 0
        self.mouse_pressed = False

    def create_pegs(self):
        pegs = []
        rows = 11
        start_y = 180  # was 150 → moves pegs lower
        horizontal_spacing = 40  # was 50 → spreads them wider
        vertical_spacing = 38    # was 35 → slightly taller rows

        for row in range(rows):
            y = start_y + row * vertical_spacing
            pegs_in_row = 3 + row
            start_x = SCREEN_WIDTH // 2 - (pegs_in_row - 1) * (horizontal_spacing / 2)
            for i in range(pegs_in_row):
                x = start_x + i * horizontal_spacing
                # jitter for variety
                pegs.append((int(x + (5 if row % 2 == 0 else -5)), int(y)))
        return pegs


    def create_reward_slots(self):
        viridis_colors = [
            (68, 1, 84),     # deep purple
            (72, 35, 116),   # dark blue-purple
            (64, 67, 135),   # blue
            (52, 94, 141),   # blue-green
            (41, 120, 142),  # teal
            (32, 144, 140),  # green-teal
            (34, 168, 132),  # green
            (68, 191, 112),  # yellow-green
            (122, 215, 81),  # light green-yellow
            (189, 223, 38)   # bright yellow
        ]

        rewards = [
    ("iPhone 16promax fullpaid", 100, viridis_colors[0]),
    ("iPhone 16promax pero installment", 90, viridis_colors[1]),
    ("iPhone 16plus fullpaid", 75, viridis_colors[2]),
    ("iPhone 16plus pero utang", 70, viridis_colors[3]),
    ("iPhone 13", 60, viridis_colors[4]),
    ("iPhone 12", 55, viridis_colors[5]),
    ("Cellphone Case", 50, viridis_colors[6]),
    ("Cellphone that goes Ayayayay", 30, viridis_colors[7]),
    ("May cellphone kana. Pwede pa yan.", 15, viridis_colors[8]),
    ("May cellphone kana. Pwede pa yan.", 15, viridis_colors[8]),
    ("Cellphone that goes Ayayayay", 30, viridis_colors[7]),
    ("Cellphone Case", 50, viridis_colors[6]),
    ("iPhone 12", 55, viridis_colors[5]),
    ("iPhone 13", 60, viridis_colors[4]),
    ("iPhone 16plus pero utang", 70, viridis_colors[3]),
    ("iPhone 16plus fullpaid", 75, viridis_colors[2]),
    ("iPhone 16promax pero installment", 90, viridis_colors[1]),
    ("iPhone 16promax fullpaid", 100, viridis_colors[0])
]
        return rewards

    def draw_splash_screen(self):
        self.screen.fill((20, 50, 80))
        title = self.font_large.render("DOST 3 EVENT", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(title, title_rect)

        subtitle = self.font_medium.render("PLINKO REWARD GAME", True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, 220))
        self.screen.blit(subtitle, subtitle_rect)

        instructions = [
            "Thank you for your evaluation!",
            "Now it's time for your reward!",
            "",
            "HOW TO PLAY:",
            "• Hold LEFT CLICK to charge power",
            "• Release to shoot ball STRAIGHT UP",
            "• Ball follows ramp to top-middle",
            "• Watch it drop through the pegs",
            "• Collect your reward at the bottom!",
            "",
            "Click anywhere to start!"
        ]

        y_start = 300
        for i, line in enumerate(instructions):
            color = CYAN
            font = self.font_tiny
            if i < 2:
                color = YELLOW
                font = self.font_small
            elif line.startswith("•") or line == "HOW TO PLAY:":
                color = WHITE
                font = self.font_small

            if line.strip():
                text = font.render(line, True, color)
                text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_start + i * 30))
                self.screen.blit(text, text_rect)

        # Decorative dots
        for i in range(40):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            color = random.choice([YELLOW, GOLD, WHITE, CYAN])
            pygame.draw.circle(self.screen, color, (x, y), 2)

    def draw_game(self):
        self.screen.fill((30, 30, 50))
        # Back button
        self.back_button.draw(self.screen)
        # Title
        title = self.font_medium.render("DOST 3 Plinko Game", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 30))
        self.screen.blit(title, title_rect)

        # Pegs
        for peg in self.pegs:
            pygame.draw.circle(self.screen, WHITE, peg, PEG_RADIUS)
            pygame.draw.circle(self.screen, SILVER, peg, PEG_RADIUS - 2)

        # Reward slots
        slot_count = len(self.reward_slots)
        slot_width = (SCREEN_WIDTH // slot_count) * 0.7  # shrink each slot
        total_width = slot_width * slot_count
        x_offset = (SCREEN_WIDTH - total_width) / 2  # center the row
        slot_y = SCREEN_HEIGHT - 80

        for i, (reward, points, color) in enumerate(self.reward_slots):
            x = x_offset + i * slot_width
            pygame.draw.rect(self.screen, color, (x, slot_y, slot_width, 80))
            pygame.draw.rect(self.screen, BLACK, (x, slot_y, slot_width, 80), 2)

            # wrap long texts
            if len(reward) > 12:
                lines = reward.split()
                mid = len(lines) // 2
                line1 = " ".join(lines[:mid])
                line2 = " ".join(lines[mid:])
                t1 = self.font_tiny.render(line1, True, BLACK)
                t2 = self.font_tiny.render(line2, True, BLACK)
                self.screen.blit(t1, t1.get_rect(center=(x + slot_width//2, slot_y + 25)))
                self.screen.blit(t2, t2.get_rect(center=(x + slot_width//2, slot_y + 50)))
            else:
                t = self.font_tiny.render(reward, True, BLACK)
                self.screen.blit(t, t.get_rect(center=(x + slot_width//2, slot_y + 40)))

        # Balls
        for ball in self.balls:
            ball.draw(self.screen)

        # Launcher
        self.launcher.draw(self.screen)

        # Instructions & power
        instruction1 = self.font_small.render("Hold LEFT CLICK to charge, release to shoot STRAIGHT UP!", True, WHITE)
        instruction1_rect = instruction1.get_rect(center=(SCREEN_WIDTH//2, 70))
        self.screen.blit(instruction1, instruction1_rect)

        if self.launcher.charging:
            power_text = self.font_small.render(f"Power: {int((self.launcher.power/self.launcher.max_power)*100)}%", True, YELLOW)
            power_rect = power_text.get_rect(center=(200, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(power_text, power_rect)

        # Peg zone boundary rails
        top_y = 150  # starting height of pegs
        bottom_y = SCREEN_HEIGHT - 80
        rail_offset_x = 200  # distance from screen edge at top

        # Left rail
        pygame.draw.line(self.screen, WHITE, (SCREEN_WIDTH//2 - rail_offset_x, top_y),
                        (0, bottom_y), 4)
        # Right rail
        pygame.draw.line(self.screen, WHITE, (SCREEN_WIDTH//2 + rail_offset_x, top_y),
                        (SCREEN_WIDTH, bottom_y), 4)


    def draw_result_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        box_width = 500
        box_height = 300
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (SCREEN_HEIGHT - box_height) // 2

        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, GOLD, (box_x, box_y, box_width, box_height), 5)

        if self.last_reward:
            congrats = self.font_medium.render("CONGRATULATIONS!", True, GOLD)
            congrats_rect = congrats.get_rect(center=(SCREEN_WIDTH//2, box_y + 60))
            self.screen.blit(congrats, congrats_rect)

            reward_text = self.font_large.render(self.last_reward[0], True, self.last_reward[2])
            reward_rect = reward_text.get_rect(center=(SCREEN_WIDTH//2, box_y + 130))
            self.screen.blit(reward_text, reward_rect)

            points_text = self.font_medium.render(f"Points: {self.last_reward[1]}", True, BLACK)
            points_rect = points_text.get_rect(center=(SCREEN_WIDTH//2, box_y + 200))
            self.screen.blit(points_text, points_rect)

            continue_text = self.font_small.render("Click anywhere to play again!", True, BLACK)
            continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH//2, box_y + 250))
            self.screen.blit(continue_text, continue_rect)

    def handle_events(self, events):
        for event in events:
            if self.state == "splash":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.state = "playing"

            elif self.state == "playing":
                if self.back_button.handle_event(event):
                    self.state = "splash"
                    self.balls = []
                    self.last_reward = None
                    self.result_timer = 0

                # Launcher charging events
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Start charging if click near launcher (or anywhere — your choice)
                    # I allow anywhere to start charging
                    self.mouse_pressed = True
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.mouse_pressed:
                        ball, power = self.launcher.launch()
                        if ball:
                            self.balls.append(ball)
                            if ball.launch_speed >= 0.5:  # consider "valid" if half power or more
                                self.launched_once = True
                            self.balls.append(ball)
                        self.mouse_pressed = False

                elif event.type == pygame.MOUSEMOTION:
                    # update hover for button
                    self.back_button.handle_event(event)

            elif self.state == "result":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.state = "playing"
                    self.balls = []
                    self.last_reward = None
                    self.result_timer = 0

                if not self.launched_once:
                    self.launcher.power = self.launcher.max_power / 2
                self.launched_once = False

    def update(self):
        if self.state == "playing":
            # update launcher charging
            self.launcher.update(self.mouse_pressed)

            # update balls
            for ball in self.balls[:]:
                ball.update(self.pegs)

                # check bottom (reward)
                if ball.y > SCREEN_HEIGHT - 100:
                    # Same width and offset as in draw_game()
                    slot_width = (SCREEN_WIDTH // len(self.reward_slots)) * 0.7
                    total_width = slot_width * len(self.reward_slots)
                    x_offset = (SCREEN_WIDTH - total_width) / 2

                    if ball.x < x_offset or ball.x > (x_offset + total_width):
                        # Outside reward boxes → game over
                        self.last_reward = ("No Prize", 0, BLACK)
                    else:
                        slot_index = int((ball.x - x_offset) // slot_width)
                        self.last_reward = self.reward_slots[slot_index]

                    try:
                        self.balls.remove(ball)
                    except ValueError:
                        pass
                    self.state = "result"
                    self.result_timer = pygame.time.get_ticks()

                # remove off-screen
                elif ball.x < -200 or ball.x > SCREEN_WIDTH + 200 or ball.y < -200 or ball.y > SCREEN_HEIGHT + 400:
                    try:
                        self.balls.remove(ball)
                    except ValueError:
                        pass

        elif self.state == "result":
            # auto return after 5s
            if pygame.time.get_ticks() - self.result_timer > 5000:
                self.state = "playing"
                self.balls = []
                self.last_reward = None
                self.result_timer = 0

    def run(self):
        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            self.handle_events(events)
            self.update()

            if self.state == "splash":
                self.draw_splash_screen()
            elif self.state == "playing":
                self.draw_game()
            elif self.state == "result":
                self.draw_game()
                self.draw_result_screen()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = PlinkoGame()
    game.run()
