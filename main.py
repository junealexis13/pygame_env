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
    def __init__(self, x, y, vx=0, vy=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = 8
        self.color = random.choice([RED, BLUE, GREEN, YELLOW, ORANGE, PURPLE])
        self.gravity = 0.3
        self.bounce = 0.7
        self.friction = 0.99
        self.active = True

    def update(self, pegs):
        if not self.active:
            return

        # Apply gravity
        self.vy += self.gravity
        
        # Apply friction
        self.vx *= self.friction
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Collision with screen boundaries
        if self.x - self.radius < 0 or self.x + self.radius > SCREEN_WIDTH:
            self.vx *= -self.bounce
            self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        
        # Collision with pegs
        for peg in pegs:
            dx = self.x - peg[0]
            dy = self.y - peg[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < self.radius + 8:  # peg radius is 8
                # Normalize collision vector
                if distance > 0:
                    dx /= distance
                    dy /= distance
                    
                    # Move ball away from peg
                    overlap = self.radius + 8 - distance
                    self.x += dx * overlap
                    self.y += dy * overlap
                    
                    # Bounce off peg
                    dot_product = self.vx * dx + self.vy * dy
                    self.vx -= 2 * dot_product * dx
                    self.vy -= 2 * dot_product * dy
                    
                    # Add some randomness
                    self.vx += random.uniform(-0.5, 0.5)
                    self.vy *= self.bounce

    def draw(self, screen):
        if self.active:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            # Add highlight for 3D effect
            highlight_pos = (int(self.x - 2), int(self.y - 2))
            pygame.draw.circle(screen, WHITE, highlight_pos, 3)

class PinballLauncher:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.power = 0
        self.max_power = 15
        self.charging = False
        self.angle = -math.pi/8  # Very gentle 22.5 degree angle for smooth glide
        self.width = 80
        self.height = 30
        
    def update(self, charging):
        self.charging = charging
        
        if charging and self.power < self.max_power:
            self.power += 0.15  # Much slower charging
        elif not charging:
            self.power = 0
    
    def draw(self, screen):
        # Draw launcher base (angled cannon style)
        pygame.draw.ellipse(screen, GRAY, 
                          (self.x - self.width//2, self.y - self.height//2, 
                           self.width, self.height))
        pygame.draw.ellipse(screen, WHITE, 
                          (self.x - self.width//2, self.y - self.height//2, 
                           self.width, self.height), 3)
        
        # Draw cannon barrel
        barrel_length = 50
        end_x = self.x + math.cos(self.angle) * barrel_length
        end_y = self.y + math.sin(self.angle) * barrel_length
        pygame.draw.line(screen, GRAY, (self.x, self.y), (end_x, end_y), 8)
        pygame.draw.line(screen, WHITE, (self.x, self.y), (end_x, end_y), 2)
        
        # Draw power indicator
        if self.charging:
            power_height = int((self.power / self.max_power) * 60)
            color = GREEN if self.power < self.max_power * 0.7 else YELLOW if self.power < self.max_power * 0.9 else RED
            pygame.draw.rect(screen, color,
                           (self.x - 80, self.y - 30 - power_height, 15, power_height))
            pygame.draw.rect(screen, WHITE,
                           (self.x - 80, self.y - 90, 15, 60), 2)
        
        # Draw trajectory preview (dotted arc)
        if self.power > 0:
            self.draw_trajectory_preview(screen)
    
    def draw_trajectory_preview(self, screen):
        # Calculate initial velocity for smooth gliding arc
        velocity_magnitude = self.power * 3.5
        vx = math.cos(self.angle) * velocity_magnitude
        vy = math.sin(self.angle) * velocity_magnitude
        
        # Simulate trajectory
        sim_x, sim_y = self.x, self.y
        gravity = 0.3
        points = []
        
        for i in range(80):  # Simulate smooth curve
            sim_x += vx
            sim_y += vy
            vy += gravity
            
            if sim_y > SCREEN_HEIGHT - 100:  # Stop at peg area
                break
                
            if i % 3 == 0:  # Every 3rd point for smooth dotted line
                points.append((int(sim_x), int(sim_y)))
        
        # Draw trajectory dots
        for point in points:
            if 0 <= point[0] <= SCREEN_WIDTH:  # Only draw visible part
                pygame.draw.circle(screen, CYAN, point, 3)
    
    def launch(self):
        if self.power > 0:
            # Calculate velocity for smooth gliding curve to middle
            velocity_magnitude = self.power * 3.5
            vx = math.cos(self.angle) * velocity_magnitude
            vy = math.sin(self.angle) * velocity_magnitude
            
            # Create ball at launcher position
            ball = Ball(self.x, self.y, vx, vy)
            launched_power = self.power
            self.power = 0
            return ball, launched_power
        return None, 0

class Button:
    def __init__(self, x, y, width, height, text, color, text_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font = pygame.font.Font(None, 36)
        self.hovered = False
        
    def draw(self, screen):
        # Draw button with hover effect
        color = tuple(min(255, c + 20) for c in self.color) if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        # Draw text
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
        self.state = "splash"  # splash, playing, result
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.font_tiny = pygame.font.Font(None, 24)
        
        # Game objects
        self.balls = []
        self.pegs = self.create_pegs()
        self.reward_slots = self.create_reward_slots()
        self.launcher = PinballLauncher(80, SCREEN_HEIGHT // 2)  # Left side launcher
        self.last_reward = None
        self.result_timer = 0
        
        # UI elements
        self.back_button = Button(20, 20, 100, 40, "Back", BLUE, WHITE)
        
        # Input state
        self.mouse_pressed = False
        
    def create_pegs(self):
        pegs = []
        # Create triangular peg pattern
        rows = 12
        start_y = 150
        for row in range(rows):
            y = start_y + row * 35
            pegs_in_row = row + 5
            start_x = SCREEN_WIDTH // 2 - (pegs_in_row - 1) * 25
            for i in range(pegs_in_row):
                x = start_x + i * 50
                pegs.append((x, y))
        return pegs
    
    def create_reward_slots(self):
        # Create 18 reward slots with normal distribution pattern
        rewards = [
            ("Small Prize", 5, BLUE),
            ("Sticker", 10, GREEN), 
            ("Pencil", 15, YELLOW),
            ("Small Prize", 5, BLUE),
            ("Eraser", 20, ORANGE),
            ("Sticker Pack", 25, PINK),
            ("Small Prize", 5, BLUE),
            ("Bookmark", 30, PURPLE),
            ("GRAND PRIZE!", 100, GOLD),  # Center - highest probability
            ("Bookmark", 30, PURPLE),
            ("Small Prize", 5, BLUE),
            ("Sticker Pack", 25, PINK),
            ("Eraser", 20, ORANGE),
            ("Small Prize", 5, BLUE),
            ("Pencil", 15, YELLOW),
            ("Sticker", 10, GREEN),
            ("Small Prize", 5, BLUE),
            ("Certificate", 50, SILVER)
        ]
        return rewards
    
    def draw_splash_screen(self):
        self.screen.fill((20, 50, 80))  # Dark blue background
        
        # Title
        title = self.font_large.render("DOST 3 EVENT", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.font_medium.render("PLINKO REWARD GAME", True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, 220))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Instructions
        instructions = [
            "Thank you for your evaluation!",
            "Now it's time for your reward!",
            "",
            "HOW TO PLAY:",
            "• Hold LEFT CLICK to charge power",
            "• Release to launch ball smoothly",
            "• Ball glides from side to middle",
            "• Watch it bounce through pegs",
            "• Collect your reward at the bottom!",
            "",
            "Click anywhere to start!"
        ]
        
        y_start = 300
        for i, line in enumerate(instructions):
            if line == "Thank you for your evaluation!" or line == "Now it's time for your reward!":
                color = YELLOW
                font = self.font_small
            elif line.startswith("•") or line == "HOW TO PLAY:":
                color = WHITE
                font = self.font_small
            else:
                color = CYAN
                font = self.font_tiny
            
            if line.strip():  # Don't render empty lines
                text = font.render(line, True, color)
                text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_start + i * 30))
                self.screen.blit(text, text_rect)
        
        # Decorative elements
        for i in range(20):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            color = random.choice([YELLOW, GOLD, WHITE, CYAN])
            pygame.draw.circle(self.screen, color, (x, y), 2)
    
    def draw_game(self):
        self.screen.fill((30, 30, 50))  # Dark background
        
        # Draw back button
        self.back_button.draw(self.screen)
        
        # Draw title
        title = self.font_medium.render("DOST 3 Plinko Game", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 30))
        self.screen.blit(title, title_rect)
        
        # Draw pegs
        for peg in self.pegs:
            pygame.draw.circle(self.screen, WHITE, peg, 8)
            pygame.draw.circle(self.screen, SILVER, peg, 6)
        
        # Draw reward slots at the bottom
        slot_width = SCREEN_WIDTH // len(self.reward_slots)
        slot_y = SCREEN_HEIGHT - 80
        
        for i, (reward, points, color) in enumerate(self.reward_slots):
            x = i * slot_width
            
            # Draw slot background
            pygame.draw.rect(self.screen, color, (x, slot_y, slot_width, 80), 0)
            pygame.draw.rect(self.screen, BLACK, (x, slot_y, slot_width, 80), 2)
            
            # Draw reward text
            if len(reward) > 8:  # Long text
                lines = reward.split()
                mid = len(lines) // 2
                line1 = " ".join(lines[:mid])
                line2 = " ".join(lines[mid:])
                
                text1 = self.font_tiny.render(line1, True, BLACK)
                text2 = self.font_tiny.render(line2, True, BLACK)
                
                text1_rect = text1.get_rect(center=(x + slot_width//2, slot_y + 25))
                text2_rect = text2.get_rect(center=(x + slot_width//2, slot_y + 45))
                
                self.screen.blit(text1, text1_rect)
                self.screen.blit(text2, text2_rect)
            else:
                text = self.font_tiny.render(reward, True, BLACK)
                text_rect = text.get_rect(center=(x + slot_width//2, slot_y + 40))
                self.screen.blit(text, text_rect)
        
        # Draw balls
        for ball in self.balls:
            ball.draw(self.screen)
        
        # Draw launcher
        self.launcher.draw(self.screen)
        
        # Instructions
        instruction1 = self.font_small.render("Hold LEFT CLICK to charge, release for smooth glide to middle!", True, WHITE)
        instruction1_rect = instruction1.get_rect(center=(SCREEN_WIDTH//2, 70))
        self.screen.blit(instruction1, instruction1_rect)
        
        # Power meter label
        if self.launcher.charging:
            power_text = self.font_small.render(f"Power: {int((self.launcher.power/self.launcher.max_power)*100)}%", True, YELLOW)
            power_rect = power_text.get_rect(center=(200, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(power_text, power_rect)
    
    def draw_result_screen(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Result box
        box_width = 500
        box_height = 300
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (SCREEN_HEIGHT - box_height) // 2
        
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, GOLD, (box_x, box_y, box_width, box_height), 5)
        
        if self.last_reward:
            # Congratulations text
            congrats = self.font_medium.render("CONGRATULATIONS!", True, GOLD)
            congrats_rect = congrats.get_rect(center=(SCREEN_WIDTH//2, box_y + 60))
            self.screen.blit(congrats, congrats_rect)
            
            # Reward text
            reward_text = self.font_large.render(self.last_reward[0], True, self.last_reward[2])
            reward_rect = reward_text.get_rect(center=(SCREEN_WIDTH//2, box_y + 130))
            self.screen.blit(reward_text, reward_rect)
            
            # Points text
            points_text = self.font_medium.render(f"Points: {self.last_reward[1]}", True, BLACK)
            points_rect = points_text.get_rect(center=(SCREEN_WIDTH//2, box_y + 180))
            self.screen.blit(points_text, points_rect)
            
            # Continue instruction
            continue_text = self.font_small.render("Click anywhere to play again!", True, BLACK)
            continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH//2, box_y + 230))
            self.screen.blit(continue_text, continue_rect)
    
    def handle_events(self, events):
        for event in events:
            if self.state == "splash":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.state = "playing"
                    
            elif self.state == "playing":
                # Handle back button
                if self.back_button.handle_event(event):
                    self.state = "splash"
                    self.balls = []
                    self.last_reward = None
                    self.result_timer = 0
                    
                # Handle launcher input
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.mouse_pressed = True
                        
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.mouse_pressed:  # Left click release
                        ball, power = self.launcher.launch()
                        if ball:
                            self.balls.append(ball)
                        self.mouse_pressed = False
                        
            elif self.state == "result":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Reset for new game
                    self.state = "playing"
                    self.balls = []
                    self.last_reward = None
                    self.result_timer = 0
    
    def update(self):
        if self.state == "playing":
            # Update launcher
            self.launcher.update(self.mouse_pressed)
            
            # Update balls
            for ball in self.balls[:]:
                ball.update(self.pegs)
                
                # Check if ball reached bottom (reward slots)
                if ball.y > SCREEN_HEIGHT - 100:
                    # Determine which slot the ball landed in
                    slot_width = SCREEN_WIDTH // len(self.reward_slots)
                    slot_index = min(len(self.reward_slots) - 1, max(0, int(ball.x // slot_width)))
                    
                    self.last_reward = self.reward_slots[slot_index]
                    self.balls.remove(ball)
                    self.state = "result"
                    self.result_timer = pygame.time.get_ticks()
                
                # Remove balls that go off screen or get stuck
                elif (ball.x < -100 or ball.x > SCREEN_WIDTH + 100 or 
                      ball.y < -100 or ball.y > SCREEN_HEIGHT + 100):
                    self.balls.remove(ball)
        
        elif self.state == "result":
            # Auto return to playing after 5 seconds
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