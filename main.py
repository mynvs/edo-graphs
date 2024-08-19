import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame
import pygame_gui
import subprocess
import sys
import threading
import json

pygame.init()
WINDOW_SIZE = (400, 235)
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption('settings')
pygame.display.set_icon(pygame.image.load('src/assets/icon2.png'))
manager = pygame_gui.UIManager(WINDOW_SIZE)

# Color constants
BACKGROUND_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
LIGHT_GRAY = (180, 180, 180)
BUTTON_COLOR = (50, 50, 50)
BUTTON_HOVER_COLOR = (70, 70, 70)
BUTTON_SELECTED_COLOR = (0, 100, 200)
BUTTON_OUTLINE_COLOR = (80, 80, 80)
BUTTON_OUTLINE_SELECTED_COLOR = (0, 150, 255)

DEFAULT_SETTINGS = {
    'EDO': 12,
    'CHORD_SIZE': 4,
    'INTERVALS': [1],
    'DIMENSIONS': 3,
    'ITERATIONS': 500,
    'DO_ALL_KEYS': True,
    'TRUNCATE_SYMBOLS': True,
    'SIMPLIFY_SYMBOLS': True,
    'INCLUSIONS': "'32', '23'",
    'EXCLUSIONS': '',
    'INCLUDE_AND': True,
    'EXCLUDE_AND': False
}

def load_settings():
    if os.path.exists('src/settings.json'):
        with open('src/settings.json', 'r') as f:
            settings = json.load(f)
            # Remove trailing comma from INCLUSIONS and EXCLUSIONS
            for key in ['INCLUSIONS', 'EXCLUSIONS']:
                if isinstance(settings.get(key), str) and settings[key].endswith(','):
                    settings[key] = settings[key].rstrip(',')
            return settings
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open('src/settings.json', 'w') as f:
        json.dump(settings, f)

current_settings = load_settings()

# Font setup
font = pygame.font.Font('src/assets/JetBrainsMono-Regular.otf', 14)

def create_label_entry(x, y, label_width, entry_width, label_text, key):
    entry = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((x+label_width+5, y), (entry_width, 25)),
                                                manager=manager)
    if key == 'INTERVALS':
        entry.set_text(','.join(map(str, current_settings[key])))
    else:
        entry.set_text(str(current_settings[key]))
    return entry

# Label rendering function
def render_label(surface, text, x, y):
    label_surface = font.render(text, True, TEXT_COLOR)
    label_rect = label_surface.get_rect(right=x, centery=y+12)
    surface.blit(label_surface, label_rect)

# Button rendering function
def render_button(surface, text, rect, selected, hovered):
    if selected:
        color = BUTTON_SELECTED_COLOR
        outline_color = BUTTON_OUTLINE_SELECTED_COLOR
        text_color = TEXT_COLOR
    elif hovered:
        color = BUTTON_HOVER_COLOR
        outline_color = BUTTON_OUTLINE_COLOR
        text_color = TEXT_COLOR
    else:
        color = BUTTON_COLOR
        outline_color = BUTTON_OUTLINE_COLOR
        text_color = LIGHT_GRAY
    
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, outline_color, rect, 1)
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)

# Adjust label positions to align their right sides
LABEL_X = 102  # Right-aligned position for labels
ENTRY_X = 105  # Left position for entry fields

edo_entry = create_label_entry(ENTRY_X, 5, 0, 72, 'EDO', 'EDO')
chord_size_entry = create_label_entry(ENTRY_X, 35, 0, 72, 'chord size', 'CHORD_SIZE')
dimensions_entry = create_label_entry(ENTRY_X+200, 5, 0, 72, 'dimensions', 'DIMENSIONS')
iterations_entry = create_label_entry(ENTRY_X+200, 35, 0, 72, 'iterations', 'ITERATIONS')
intervals_entry = create_label_entry(ENTRY_X, 65, 0, 272, 'intervals', 'INTERVALS')
inclusions_entry = create_label_entry(ENTRY_X, 95, 0, 222, 'include', 'INCLUSIONS')
exclusions_entry = create_label_entry(ENTRY_X, 125, 0, 222, 'exclude', 'EXCLUSIONS')

class Button:
    def __init__(self, rect, text, key):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.key = key
        self.is_selected = current_settings.get(key, False)
        self.is_hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.key in current_settings:
                    self.is_selected = not self.is_selected
                return True
        return False

    def draw(self, surface):
        render_button(surface, self.text, self.rect, self.is_selected, self.is_hovered)

do_all_keys = Button((20, 160, 105, 25), 'do all keys', 'DO_ALL_KEYS')
truncate_symbols = Button((210, 160, 80, 25), 'truncate', 'TRUNCATE_SYMBOLS')
simplify_symbols = Button((300, 160, 80, 25), 'omit ".0"', 'SIMPLIFY_SYMBOLS')
include_and = Button((340, 95, 40, 25), 'AND', 'INCLUDE_AND')
exclude_and = Button((340, 125, 40, 25), 'AND', 'EXCLUDE_AND')

run_button = Button((20, 195, 70, 25), 'run', 'RUN')
reset_button = Button((310, 195, 70, 25), 'reset', 'RESET')

buttons = [do_all_keys, truncate_symbols, simplify_symbols, include_and, exclude_and, run_button, reset_button]

def update_ui_with_settings():
    edo_entry.set_text(str(current_settings['EDO']))
    chord_size_entry.set_text(str(current_settings['CHORD_SIZE']))
    intervals_entry.set_text(','.join(map(str, current_settings['INTERVALS'])))
    dimensions_entry.set_text(str(current_settings['DIMENSIONS']))
    iterations_entry.set_text(str(current_settings['ITERATIONS']))
    
    inclusions_entry.set_text(str(current_settings['INCLUSIONS']))
    exclusions_entry.set_text(str(current_settings['EXCLUSIONS']))
    
    for button in buttons:
        if button.key in current_settings:
            button.is_selected = current_settings[button.key]

def run_program():
    try:
        current_settings['EDO'] = int(edo_entry.get_text())
        current_settings['CHORD_SIZE'] = int(chord_size_entry.get_text())
        current_settings['INTERVALS'] = [int(i.strip()) for i in intervals_entry.get_text().split(',') if i.strip()]
        current_settings['DIMENSIONS'] = int(dimensions_entry.get_text())
        current_settings['ITERATIONS'] = int(iterations_entry.get_text())
        current_settings['DO_ALL_KEYS'] = do_all_keys.is_selected
        current_settings['TRUNCATE_SYMBOLS'] = truncate_symbols.is_selected
        current_settings['SIMPLIFY_SYMBOLS'] = simplify_symbols.is_selected
        
        inclusions = inclusions_entry.get_text()
        exclusions = exclusions_entry.get_text()
        
        # Only add a comma if there's more than one item
        if inclusions and not (inclusions == 'False'):
            current_settings['INCLUSIONS'] = inclusions if ',' in inclusions else inclusions + ','
        else:
            current_settings['INCLUSIONS'] = False
        
        if exclusions and not (exclusions == 'False'):
            current_settings['EXCLUSIONS'] = exclusions if ',' in exclusions else exclusions + ','
        else:
            current_settings['EXCLUSIONS'] = False

        current_settings['INCLUDE_AND'] = include_and.is_selected
        current_settings['EXCLUDE_AND'] = exclude_and.is_selected
        
        save_settings(current_settings)
        
        with open('src/temp_settings.py', 'w') as f:
            for key, value in current_settings.items():
                f.write(f"{key} = {value}\n")
        
        subprocess.run([sys.executable, 'src/edo_graphs.py'])
    except ValueError as e:
        print(f"error in input: {e}")
    except Exception as e:
        print(f"an error occurred: {e}")

clock = pygame.time.Clock()
is_running = True

while is_running:
    time_delta = clock.tick(30)/1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False

        for button in buttons:
            if button.handle_event(event):
                if button == run_button:
                    threading.Thread(target=run_program, daemon=True).start()
                elif button == reset_button:
                    current_settings = DEFAULT_SETTINGS.copy()
                    update_ui_with_settings()

        manager.process_events(event)

    manager.update(time_delta)

    screen.fill(BACKGROUND_COLOR)
    manager.draw_ui(screen)

    # Render labels
    render_label(screen, 'EDO', LABEL_X, 5)
    render_label(screen, 'chord size', LABEL_X, 35)
    render_label(screen, 'dimensions', LABEL_X+200, 5)
    render_label(screen, 'iterations', LABEL_X+200, 35)
    render_label(screen, 'intervals', LABEL_X, 65)
    render_label(screen, 'include', LABEL_X, 95)
    render_label(screen, 'exclude', LABEL_X, 125)

    # Render buttons
    for button in buttons:
        button.draw(screen)

    pygame.display.update()

pygame.quit()