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
        pygame.draw.rect(screen, COLORS['WHITE'], self.rect, 2)
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
