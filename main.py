import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame
import pygame_gui
import subprocess
import sys
import threading
import json
import os

pygame.init()
WINDOW_SIZE = (400, 250)
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption('settings')
manager = pygame_gui.UIManager(WINDOW_SIZE)

DEFAULT_SETTINGS = {
    'EDO': 12,
    'CHORD_SIZE': 4,
    'INTERVALS': [1],
    'DIMENSIONS': 4,
    'ITERATIONS': 500,
    'DO_ALL_KEYS': True,
    'TRUNCATE_SYMBOLS': True,
    'SIMPLIFY_SYMBOLS': True,
    'INCLUSIONS': "'32', '23'",
    'EXCLUSIONS': 'False',
    'INCLUDE_AND': True,
    'EXCLUDE_AND': False
}

def load_settings():
    if os.path.exists('src/settings.json'):
        with open('src/settings.json', 'r') as f:
            return json.load(f)
    return DEFAULT_SETTINGS.copy()
def save_settings(settings):
    with open('src/settings.json', 'w') as f:
        json.dump(settings, f)
current_settings = load_settings()

def create_label_entry(x, y, label_width, entry_width, label_text, key):
    label = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((x, y), (label_width, 25)),
                                        text=label_text,
                                        manager=manager)
    entry = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((x+label_width+5, y), (entry_width, 25)),
                                                manager=manager)
    if key == 'INTERVALS':
        entry.set_text(','.join(map(str, current_settings[key])))
    else:
        entry.set_text(str(current_settings[key]))
    return entry

edo_entry = create_label_entry(20, 20, 85, 70, 'EDO:', 'EDO')
chord_size_entry = create_label_entry(20, 50, 85, 70, 'chord size:', 'CHORD_SIZE')
dimensions_entry = create_label_entry(220, 20, 85, 70, 'dimensions:', 'DIMENSIONS')
iterations_entry = create_label_entry(220, 50, 85, 70, 'iterations:', 'ITERATIONS')
intervals_entry = create_label_entry(20, 80, 85, 270, 'intervals:', 'INTERVALS')
inclusions_entry = create_label_entry(20, 110, 85, 195, 'include:', 'INCLUSIONS')
exclusions_entry = create_label_entry(20, 140, 85, 195, 'exclude:', 'EXCLUSIONS')

def create_toggle_button(x, y, width, text, key):
    button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((x, y), (width, 25)),
                                          text=text,
                                          manager=manager)
    if current_settings[key]:
        button.select()
    return button

do_all_keys = create_toggle_button(20, 180, 110, 'do all keys', 'DO_ALL_KEYS')
truncate_symbols = create_toggle_button(135, 180, 130, 'truncate symbols', 'TRUNCATE_SYMBOLS')
simplify_symbols = create_toggle_button(270, 180, 110, 'omit ".0"', 'SIMPLIFY_SYMBOLS')
include_and = create_toggle_button(310, 110, 70, 'AND', 'INCLUDE_AND')
exclude_and = create_toggle_button(310, 140, 70, 'AND', 'EXCLUDE_AND')

run_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((20, 210), (80, 30)),
                                          text='run',
                                          manager=manager)
reset_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((300, 210), (80, 30)),
                                            text='reset',
                                            manager=manager)

def update_ui_with_settings():
    edo_entry.set_text(str(current_settings['EDO']))
    chord_size_entry.set_text(str(current_settings['CHORD_SIZE']))
    intervals_entry.set_text(','.join(map(str, current_settings['INTERVALS'])))
    dimensions_entry.set_text(str(current_settings['DIMENSIONS']))
    iterations_entry.set_text(str(current_settings['ITERATIONS']))
    inclusions_entry.set_text(str(current_settings['INCLUSIONS']))
    exclusions_entry.set_text(str(current_settings['EXCLUSIONS']))
    
    for button, key in [(do_all_keys, 'DO_ALL_KEYS'), 
                        (truncate_symbols, 'TRUNCATE_SYMBOLS'),
                        (simplify_symbols, 'SIMPLIFY_SYMBOLS'),
                        (include_and, 'INCLUDE_AND'),
                        (exclude_and, 'EXCLUDE_AND')]:
        if current_settings[key]:
            button.select()
        else:
            button.unselect()

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
        current_settings['INCLUSIONS'] = inclusions+',' if inclusions and not (inclusions == 'False') else False
        current_settings['EXCLUSIONS'] = exclusions+',' if exclusions and not (exclusions == 'False') else False
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

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == run_button:
                threading.Thread(target=run_program, daemon=True).start()
            elif event.ui_element == reset_button:
                current_settings = DEFAULT_SETTINGS.copy()
                update_ui_with_settings()
            elif event.ui_element in [do_all_keys, truncate_symbols, simplify_symbols, include_and, exclude_and]:
                event.ui_element.is_selected = not event.ui_element.is_selected

        manager.process_events(event)

    manager.update(time_delta)

    screen.fill((0, 0, 0))
    manager.draw_ui(screen)

    pygame.display.update()

pygame.quit()