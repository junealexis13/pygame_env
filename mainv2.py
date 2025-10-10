import pygame
import random
import math
import sys
import tomllib, os
from datetime import datetime

# Game comps
from ball import Ball
from launcher import PinballLauncher
from buttons import Button 
from prizemanager import PrizeManager

# Initialize Pygame
pygame.init()

with open('gameconfig.toml', 'rb') as conf:
    GAME_CONFIGS = tomllib.load(conf)
    VIEW = GAME_CONFIGS['view_parameters']
    COLORS = GAME_CONFIGS['colormaps']
    BALLPHYSICS = GAME_CONFIGS['ball_physics']
    PEG_DISTANCE = GAME_CONFIGS['peg_distances']

SCREEN_WIDTH = VIEW['SCREEN_WIDTH']
SCREEN_HEIGHT = VIEW['SCREEN_HEIGHT']
PEG_RADIUS = VIEW['PEG_RADIUS']
FPS = VIEW['FPS']

class PlinkoGame:
    def __init__(self,initial_prizes, seed=None):
        # Set seed FIRST before any random calls

        #####INIT#####
        

        self.seed = seed if seed is not None else int(datetime.now().timestamp() * 1000000)
        random.seed(self.seed)

        print(f'GAMEINSTANCE with seed {random.seed(self.seed)} - {datetime.now()} ')
        self.ball_rng = random.Random(self.seed + 1)
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("DOST 3 Plinko Reward Game")
        self.clock = pygame.time.Clock()
        
        self.logo = pygame.image.load("dost_logo.png").convert_alpha()
        self.logo = pygame.transform.smoothscale(self.logo, (150, 150))

        # Game states
        self.launched_once = False
        self.state = "splash"
        self.font_large = pygame.font.Font(None, 65)
        self.font_medium = pygame.font.Font(None, 42)
        self.font_small = pygame.font.Font(None, 30)
        self.font_tiny = pygame.font.Font(None, 12)

        # Game objects - create AFTER seeding
        self.ball_rng = random.Random(self.seed + 1)

        self.balls = []
        self.pegs = self.create_pegs()
        self.reward_slots = self.create_reward_slots()
        self.prize_manager = PrizeManager(initial_prizes=initial_prizes)
        self.launcher = PinballLauncher(80, SCREEN_HEIGHT // 2 + 60, ball_rng=self.ball_rng)
        self.back_button = Button(20, 20, 100, 40, "Back", COLORS['BLUE'], COLORS['WHITE'])

        # UI / result vars
        self.last_reward = None
        self.result_timer = 0
        self.mouse_pressed = False

        self.recorded_outcomes = []
        
        # Store splash screen dots deterministically
        self.splash_dots = [(random.randint(0, SCREEN_WIDTH), 
                            random.randint(0, SCREEN_HEIGHT),
                            random.choice([COLORS['YELLOW'], COLORS['GOLD'], COLORS['WHITE'], COLORS['CYAN']]))
                           for _ in range(40)]

    def create_pegs(self):
        pegs = []
        rows = 11
        start_y = 180
        horizontal_spacing = PEG_DISTANCE['h_spacing']
        vertical_spacing = PEG_DISTANCE['v_spacing']

        for row in range(rows):
            y = start_y + row * vertical_spacing
            pegs_in_row = 3 + row
            start_x = SCREEN_WIDTH // 2 - (pegs_in_row - 1) * (horizontal_spacing / 2)
            for i in range(pegs_in_row):
                x = start_x + i * horizontal_spacing
                # Deterministic jitter based on seed
                jitter = 5 if row % 2 == 0 else -5
                pegs.append((int(x + jitter), int(y)))
        return pegs

    def create_reward_slots(self):
        very_common_color = (122, 215, 81)
        common_color = (68, 191, 112)
        uncommon_color = (52, 94, 141)
        grand_prize_color = (189, 223, 38)

        rewards = [
            ("Power Bank", 10, grand_prize_color, 0.35),
            ("Newton's Cradle", 30, uncommon_color, 0.8),
            ("32GB Flash Drive", 20, common_color, 1.0),
            ("Gcash Load", 100, grand_prize_color, 2.5),
            ("32GB Flash Drive", 20, common_color, 1.0),
            ("Newton's Cradle", 30, uncommon_color, 0.8),
            ("Power Bank", 10, grand_prize_color, 0.35)
        ]
        return rewards

    def draw_splash_screen(self):
        self.screen.fill((20, 50, 80))

        logo_rect = self.logo.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.20))
        self.screen.blit(self.logo, logo_rect)
        
        subtitle = self.font_medium.render("PLINKO REWARD GAME", True, COLORS['WHITE'])
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT * 0.35))
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
            color = COLORS['CYAN']
            font = self.font_tiny
            if i < 2:
                color = COLORS['YELLOW']
                font = self.font_small
            elif line.startswith("•") or line == "HOW TO PLAY:":
                color = COLORS['WHITE']
                font = self.font_small

            if line.strip():
                text = font.render(line, True, color)
                text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_start + i * 30))
                self.screen.blit(text, text_rect)

        # Use pre-generated dots for determinism
        for x, y, color in self.splash_dots:
            pygame.draw.circle(self.screen, color, (x, y), 2)

    def draw_game(self):
        self.screen.fill((30, 30, 50))
        self.back_button.draw(self.screen)
        
        title = self.font_medium.render("DOST 3 Plinko Game", True, COLORS['GOLD'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 30))
        self.screen.blit(title, title_rect)

        for peg in self.pegs:
            pygame.draw.circle(self.screen, COLORS['WHITE'], peg, PEG_RADIUS)
            pygame.draw.circle(self.screen, COLORS['SILVER'], peg, PEG_RADIUS - 2)

        slot_count = len(self.reward_slots)
        slot_y = SCREEN_HEIGHT - 80
        base_slot_width = 80

        total_width = sum(base_slot_width * mult for _, _, _, mult in self.reward_slots)
        x_offset = (SCREEN_WIDTH - total_width) / 2

        current_x = x_offset
        for i, (reward, points, color, width_mult) in enumerate(self.reward_slots):
            slot_width = base_slot_width * width_mult
            pygame.draw.rect(self.screen, color, (current_x, slot_y, slot_width, 80))
            pygame.draw.rect(self.screen, COLORS['BLACK'], (current_x, slot_y, slot_width, 80), 2)
            current_x += slot_width

        for ball in self.balls:
            ball.draw(self.screen)

        self.launcher.draw(self.screen)

        instruction1 = self.font_small.render("Hold LEFT CLICK to charge, release to shoot STRAIGHT UP!", True, COLORS['WHITE'])
        instruction1_rect = instruction1.get_rect(center=(SCREEN_WIDTH//2, 70))
        self.screen.blit(instruction1, instruction1_rect)

        if self.launcher.charging:
            power_text = self.font_small.render(f"Power: {int((self.launcher.power/self.launcher.max_power)*100)}%", True, COLORS['YELLOW'])
            power_rect = power_text.get_rect(center=(200, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(power_text, power_rect)

        top_y = 120
        bottom_y = SCREEN_HEIGHT - 90
        rail_offset_x = 200

        pygame.draw.line(self.screen, COLORS['WHITE'], (SCREEN_WIDTH//2 - rail_offset_x, top_y),
                        (0, bottom_y), 4)
        pygame.draw.line(self.screen, COLORS['WHITE'], (SCREEN_WIDTH//2 + rail_offset_x, top_y),
                        (SCREEN_WIDTH, bottom_y), 4)

    def draw_result_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(COLORS['BLACK'])
        self.screen.blit(overlay, (0, 0))

        box_width = 500
        box_height = 300
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (SCREEN_HEIGHT - box_height) // 2

        pygame.draw.rect(self.screen, COLORS['WHITE'], (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, COLORS['GOLD'], (box_x, box_y, box_width, box_height), 5)

        if self.last_reward:
            if self.last_reward[0] == "No Prize":
                message = self.font_medium.render("Better luck next time", True, COLORS['RED'])
                message_rect = message.get_rect(center=(SCREEN_WIDTH//2, box_y + 100))
                self.screen.blit(message, message_rect)
            else:
                congrats = self.font_medium.render("CONGRATULATIONS!", True, COLORS['GOLD'])
                congrats_rect = congrats.get_rect(center=(SCREEN_WIDTH//2, box_y + 60))
                self.screen.blit(congrats, congrats_rect)

                reward_text = self.font_large.render(self.last_reward[0], True, self.last_reward[2])
                reward_rect = reward_text.get_rect(center=(SCREEN_WIDTH//2, box_y + 130))
                self.screen.blit(reward_text, reward_rect)

            continue_text = self.font_small.render("Click anywhere to play again!", True, COLORS['BLACK'])
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

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.mouse_pressed = True
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.mouse_pressed:
                        if not any(ball.active for ball in self.balls):
                            ball, power = self.launcher.launch()
                            if ball:
                                ball.rng = self.ball_rng
                                self.balls.append(ball)
                                if ball.launch_speed >= 0.5:
                                    self.launched_once = True
                        self.mouse_pressed = False

                elif event.type == pygame.MOUSEMOTION:
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
            self.launcher.update(self.mouse_pressed)

            for ball in self.balls[:]:
                ball.update(self.pegs)
                if ball.y > SCREEN_HEIGHT - 100:
                    base_slot_width = 80
                    total_width = sum(base_slot_width * mult for _, _, _, mult in self.reward_slots)
                    x_offset = (SCREEN_WIDTH - total_width) / 2

                    reward_found = False
                    current_x = x_offset
                    for slot in self.reward_slots:
                        slot_width = base_slot_width * slot[3]
                        if current_x <= ball.x < current_x + slot_width:
                            prize_name = slot[0]
                            if self.prize_manager.get_prize_count(prize_name) > 0:
                                self.last_reward = slot
                                self.prize_manager.decrement_prize(prize_name)
                            else:
                                self.last_reward = ("No Prize", 0, COLORS['BLACK'], 1.0)
                            reward_found = True  # <-- FIX: Mark reward as found
                            break                # <-- FIX: Exit loop after assigning reward
                        current_x += slot_width

                    if not reward_found:
                        self.last_reward = ("No Prize", 0, COLORS['BLACK'], 1.0)

                    try:
                        self.balls.remove(ball)
                    except ValueError:
                        pass

                    self.recorded_outcomes.append(self.last_reward)
                    print(f"Outcome {len(self.recorded_outcomes)}: {self.last_reward[0]}")

                    self.state = "result"
                    self.result_timer = pygame.time.get_ticks()

                elif ball.x < -200 or ball.x > SCREEN_WIDTH + 200 or ball.y < -200 or ball.y > SCREEN_HEIGHT + 400:
                    try:
                        self.balls.remove(ball)
                    except ValueError:
                        pass

        elif self.state == "result":
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

        self.prize_manager.close()
        pygame.quit()
        print(f"\nFinal outcomes with seed {self.seed}:")
        for i, outcome in enumerate(self.recorded_outcomes, 1):
            print(f"  {i}. {outcome[0]}")
        sys.exit()

if __name__ == "__main__":
    import json

    with open("/Users/junealexis.santos13gmail.com/Documents/projects/pygame_env/prizes.json", 'rb') as prz:
        prize = json.load(prz)

    
        
    seed = 123456
    game = PlinkoGame(seed=seed,initial_prizes=prize)
    game.run()