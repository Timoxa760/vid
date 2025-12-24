import cv2
import numpy as np
import os
import sys
import time
import shutil
import subprocess
from datetime import datetime

# ANSI цвета для интерфейса
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

# Цвета для ASCII арта (только для терминала)
ASCII_COLORS = {
    'red': '\033[91m',
    'green': '\033[92m', 
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
    'reset': '\033[0m'
}

# RGB цвета для сохранения в файлы
RGB_COLORS = {
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'yellow': (255, 255, 0),
    'blue': (0, 0, 255),
    'magenta': (255, 0, 255),
    'cyan': (0, 255, 255),
    'white': (255, 255, 255),
    'black': (0, 0, 0)
}

# Цвета фона для сохранения
BACKGROUND_COLORS = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'gray': (128, 128, 128),
    'dark_gray': (64, 64, 64),
    'light_gray': (192, 192, 192)
}

def check_ffmpeg():
    """Проверяет наличие ffmpeg в системе"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_downloads_folder():
    """Получает путь к папке Загрузки"""
    if os.name == 'nt':  # Windows
        downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
    else:  # Linux/Mac
        downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
    
    # Создаем подпапку для ASCII видео
    ascii_downloads = os.path.join(downloads, 'ASCII_Videos')
    if not os.path.exists(ascii_downloads):
        os.makedirs(ascii_downloads)
    
    return ascii_downloads

def create_project_folder(video_path, settings):
    """Создает уникальную папку для проекта на основе настроек"""
    downloads_folder = get_downloads_folder()
    
    # Получаем имя файла без расширения
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # Создаем уникальный идентификатор на основе настроек
    settings_hash = ""
    if settings['invert']:
        settings_hash += "inv_"
    if settings['transparent']:
        settings_hash += f"tr{settings['threshold']}_"
    if settings['color']:
        settings_hash += f"{settings['color']}_"
    if settings['random_colors']:
        settings_hash += "rand_"
    if settings['width']:
        settings_hash += f"w{settings['width']}_"
    if settings['background'] != 'black':
        settings_hash += f"bg{settings['background']}_"
    
    # Убираем последний символ подчеркивания если есть
    if settings_hash.endswith('_'):
        settings_hash = settings_hash[:-1]
    
    # Если нет особых настроек, используем timestamp
    if not settings_hash:
        settings_hash = datetime.now().strftime("%H%M%S")
    
    # Создаем имя папки
    project_name = f"{video_name}_{settings_hash}"
    project_path = os.path.join(downloads_folder, project_name)
    
    # Создаем подпапки
    frames_dir = os.path.join(project_path, 'frames')
    video_dir = os.path.join(project_path, 'videos')
    
    if not os.path.exists(frames_dir):
        os.makedirs(frames_dir)
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)
    
    return project_path, frames_dir, video_dir

def clear_screen():
    """Очистка экрана"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Заголовок меню"""
    clear_screen()
    print("=" * 60)
    print(f"{Colors.CYAN}{title:^60}{Colors.RESET}")
    print("=" * 60)

def print_menu_option(number, text, selected=False):
    """Пункт меню"""
    marker = f"{Colors.GREEN}[x]{Colors.RESET}" if selected else f"{Colors.WHITE}[ ]{Colors.RESET}"
    print(f"  {Colors.YELLOW}{number:2d}.{Colors.RESET} {marker} {text}")

def get_video_path():
    """Получение пути к видео"""
    while True:
        print_header("ВЫБОР ВИДЕО ФАЙЛА")
        print(f"{Colors.WHITE}Введите путь к видео файлу:{Colors.RESET}")
        print(f"{Colors.BLUE}Пример: C:/videos/my_video.mp4{Colors.RESET}")
        print()
        
        video_path = input(f"{Colors.GREEN}> {Colors.RESET}").strip()
        
        if not video_path:
            continue
            
        if os.path.exists(video_path):
            return video_path
        else:
            print(f"{Colors.RED}Файл не найден! Проверьте путь.{Colors.RESET}")
            input(f"{Colors.YELLOW}Нажмите Enter для продолжения...{Colors.RESET}")

def display_settings_menu():
    """Меню настроек"""
    downloads_folder = get_downloads_folder()
    has_ffmpeg = check_ffmpeg()
    
    settings = {
        'width': None,  # Авто-размер по умолчанию для терминала
        'invert': False,
        'transparent': False,
        'threshold': 150,
        'color': None,
        'random_colors': False,
        'save_txt': True,
        'save_frames': False,
        'save_video': False,
        'loop': False,
        'background': 'black',  # Цвет фона по умолчанию
        'font_quality': 'high'  # Качество шрифта
    }
    
    while True:
        print_header("НАСТРОЙКИ КОНВЕРТАЦИИ")
        
        # Показываем путь сохранения
        print(f"{Colors.GREEN}Сохранение в: {downloads_folder}{Colors.RESET}")
        print(f"{Colors.BLUE}Разрешение PNG/Video: как у исходного видео{Colors.RESET}")
        
        # Показываем статус ffmpeg
        ffmpeg_status = f"{Colors.GREEN}доступен{Colors.RESET}" if has_ffmpeg else f"{Colors.RED}не доступен{Colors.RESET}"
        print(f"{Colors.WHITE}FFmpeg: {ffmpeg_status}{Colors.RESET}")
        print()
        
        # Основные настройки
        print(f"{Colors.WHITE}Основные настройки:{Colors.RESET}")
        width_display = settings['width'] if settings['width'] else "авто"
        print_menu_option(1, f"Ширина в терминале: {width_display} символов")
        
        # Стиль (можно выбрать несколько)
        style_text = []
        if settings['invert']:
            style_text.append("инвертированный")
        if settings['transparent']:
            style_text.append("прозрачный фон")
        style_display = ", ".join(style_text) if style_text else "обычный"
        print_menu_option(2, f"Стиль: {style_display}")
        
        if settings['transparent']:
            print_menu_option(3, f"Порог прозрачности: {settings['threshold']}")
        
        # Цвет текста
        color_display = "случайные" if settings['random_colors'] else settings['color'] if settings['color'] else "нет"
        print_menu_option(4, f"Цвет текста: {color_display}")
        
        # Цвет фона
        bg_display = settings['background']
        print_menu_option(5, f"Цвет фона: {bg_display}")
        
        # Качество шрифта
        quality_display = settings['font_quality']
        print_menu_option(6, f"Качество шрифта: {quality_display}")
        
        # Сохранение
        print(f"\n{Colors.WHITE}Сохранение:{Colors.RESET}")
        save_options = []
        if settings['save_txt']:
            save_options.append("текст")
        if settings['save_frames']:
            save_options.append("PNG (оригинальное разрешение)")
        if settings['save_video']:
            if has_ffmpeg:
                save_options.append("видео (оригинальное разрешение)")
            else:
                save_options.append("видео (требуется ffmpeg)")
        save_display = ", ".join(save_options) if save_options else "только просмотр"
        print_menu_option(7, f"Сохранение: {save_display}")
        
        # Дополнительные настройки
        print(f"\n{Colors.WHITE}Дополнительно:{Colors.RESET}")
        loop_display = "да" if settings['loop'] else "нет"
        print_menu_option(8, f"Зацикливание: {loop_display}")
        
        print(f"\n{Colors.WHITE}Управление:{Colors.RESET}")
        print(f"  {Colors.YELLOW} 9.{Colors.RESET} {Colors.GREEN}Начать конвертацию{Colors.RESET}")
        print(f"  {Colors.YELLOW} 0.{Colors.RESET} {Colors.RED}Выход{Colors.RESET}")
        
        print(f"\n{Colors.BLUE}Выберите пункт меню (0-9):{Colors.RESET}")
        
        try:
            choice = input(f"{Colors.GREEN}> {Colors.RESET}").strip()
            
            if choice == '0':
                return None
            elif choice == '1':
                settings['width'] = get_width_setting()
            elif choice == '2':
                settings = get_style_settings(settings)
            elif choice == '3' and settings['transparent']:
                settings['threshold'] = get_threshold_setting()
            elif choice == '4':
                settings = get_color_settings(settings)
            elif choice == '5':
                settings = get_background_settings(settings)
            elif choice == '6':
                settings = get_font_quality_settings(settings)
            elif choice == '7':
                settings = get_save_settings(settings, has_ffmpeg)
            elif choice == '8':
                settings['loop'] = not settings['loop']
            elif choice == '9':
                return settings
            else:
                print(f"{Colors.RED}Неверный выбор!{Colors.RESET}")
                time.sleep(1)
                
        except KeyboardInterrupt:
            return None

def get_width_setting():
    """Настройка ширины для терминала"""
    print_header("НАСТРОЙКА ШИРИНЫ ДЛЯ ТЕРМИНАЛА")
    print(f"{Colors.WHITE}Введите ширину в символах:{Colors.RESET}")
    print(f"{Colors.BLUE}Рекомендация: 80-150 символов{Colors.RESET}")
    print(f"{Colors.YELLOW}Оставьте пустым для автоматического определения{Colors.RESET}")
    print(f"{Colors.MAGENTA}Примечание: PNG и видео сохраняются в оригинальном разрешении{Colors.RESET}")
    print()
    
    width = input(f"{Colors.GREEN}> {Colors.RESET}").strip()
    return int(width) if width.isdigit() else None

def get_style_settings(settings):
    """Настройка стиля (можно выбрать несколько)"""
    while True:
        print_header("НАСТРОЙКА СТИЛЯ")
        print(f"{Colors.WHITE}Выберите стили (можно несколько):{Colors.RESET}")
        
        print_menu_option(1, "Инвертированный", settings['invert'])
        print_menu_option(2, "Прозрачный фон", settings['transparent'])
        print_menu_option(3, "Обычный (сбросить все)", False)
        print()
        print(f"{Colors.BLUE}Введите номера через пробел (например: 1 2){Colors.RESET}")
        print()
        
        choice = input(f"{Colors.GREEN}> {Colors.RESET}").strip()
        
        if choice == '3':
            settings['invert'] = False
            settings['transparent'] = False
            return settings
        
        choices = choice.split()
        settings['invert'] = '1' in choices
        settings['transparent'] = '2' in choices
        return settings

def get_threshold_setting():
    """Настройка порога прозрачности"""
    print_header("ПОРОГ ПРОЗРАЧНОСТИ")
    print(f"{Colors.WHITE}Введите порог прозрачности (0-255):{Colors.RESET}")
    print(f"{Colors.BLUE}Чем выше значение, тем больше прозрачных областей{Colors.RESET}")
    print(f"{Colors.YELLOW}Рекомендация: 100-200{Colors.RESET}")
    print()
    
    while True:
        threshold = input(f"{Colors.GREEN}> {Colors.RESET}").strip()
        if threshold.isdigit() and 0 <= int(threshold) <= 255:
            return int(threshold)
        print(f"{Colors.RED}Введите число от 0 до 255!{Colors.RESET}")

def get_color_settings(settings):
    """Настройка цвета текста"""
    print_header("НАСТРОЙКА ЦВЕТА ТЕКСТА")
    print(f"{Colors.WHITE}Выберите цвет текста:{Colors.RESET}")
    
    colors_list = [
        ('1', 'Без цвета', None),
        ('2', 'Красный', 'red'),
        ('3', 'Зеленый', 'green'),
        ('4', 'Синий', 'blue'),
        ('5', 'Желтый', 'yellow'),
        ('6', 'Случайные цвета', 'random')
    ]
    
    for num, text, color_val in colors_list:
        selected = False
        if color_val == 'random' and settings['random_colors']:
            selected = True
        elif settings['color'] == color_val:
            selected = True
        print_menu_option(int(num), text, selected)
    
    print()
    choice = input(f"{Colors.GREEN}> {Colors.RESET}").strip()
    
    if choice == '1':
        settings['color'] = None
        settings['random_colors'] = False
    elif choice == '6':
        settings['color'] = None
        settings['random_colors'] = True
    elif choice in ['2', '3', '4', '5']:
        color_map = {'2': 'red', '3': 'green', '4': 'blue', '5': 'yellow'}
        settings['color'] = color_map[choice]
        settings['random_colors'] = False
    
    return settings

def get_background_settings(settings):
    """Настройка цвета фона"""
    print_header("НАСТРОЙКА ЦВЕТА ФОНА")
    print(f"{Colors.WHITE}Выберите цвет фона для сохранения:{Colors.RESET}")
    
    bg_colors = [
        ('1', 'Черный', 'black'),
        ('2', 'Белый', 'white'),
        ('3', 'Серый', 'gray'),
        ('4', 'Темно-серый', 'dark_gray'),
        ('5', 'Светло-серый', 'light_gray')
    ]
    
    for num, text, bg_val in bg_colors:
        selected = (settings['background'] == bg_val)
        print_menu_option(int(num), text, selected)
    
    print()
    choice = input(f"{Colors.GREEN}> {Colors.RESET}").strip()
    
    bg_map = {'1': 'black', '2': 'white', '3': 'gray', '4': 'dark_gray', '5': 'light_gray'}
    settings['background'] = bg_map.get(choice, 'black')
    
    return settings

def get_font_quality_settings(settings):
    """Настройка качества шрифта"""
    print_header("НАСТРОЙКА КАЧЕСТВА ШРИФТА")
    print(f"{Colors.WHITE}Выберите качество шрифта для PNG/Video:{Colors.RESET}")
    
    qualities = [
        ('1', 'Высокое (четкие символы, большие файлы)', 'high'),
        ('2', 'Среднее (баланс качества и размера)', 'medium'),
        ('3', 'Низкое (маленькие файлы)', 'low')
    ]
    
    for num, text, qual_val in qualities:
        selected = (settings['font_quality'] == qual_val)
        print_menu_option(int(num), text, selected)
    
    print()
    choice = input(f"{Colors.GREEN}> {Colors.RESET}").strip()
    
    qual_map = {'1': 'high', '2': 'medium', '3': 'low'}
    settings['font_quality'] = qual_map.get(choice, 'high')
    
    return settings

def get_save_settings(settings, has_ffmpeg):
    """Настройка сохранения (можно выбрать несколько)"""
    print_header("НАСТРОЙКА СОХРАНЕНИЕ")
    print(f"{Colors.WHITE}Выберите варианты сохранения:{Colors.RESET}")
    print(f"{Colors.MAGENTA}PNG и видео сохраняются в оригинальном разрешении{Colors.RESET}")
    print()
    
    options = [
        (1, "Текстовые файлы (.txt)", settings['save_txt']),
        (2, f"PNG изображения ({settings['font_quality']} качество)", settings['save_frames'])
    ]
    
    if has_ffmpeg:
        options.append((3, f"Видео файл (.mp4) ({settings['font_quality']} качество)", settings['save_video']))
    else:
        options.append((3, "Видео файл (.mp4) - ffmpeg не найден", False))
    
    options.append((4, "Только просмотр (сбросить все)", False))
    
    for num, text, selected in options:
        print_menu_option(num, text, selected)
    
    print()
    print(f"{Colors.BLUE}Введите номера через пробел{Colors.RESET}")
    print()
    
    choice = input(f"{Colors.GREEN}> {Colors.RESET}").strip()
    
    if choice == '4':
        settings['save_txt'] = False
        settings['save_frames'] = False
        settings['save_video'] = False
        return settings
    
    choices = choice.split()
    settings['save_txt'] = '1' in choices
    settings['save_frames'] = '2' in choices
    settings['save_video'] = '3' in choices and has_ffmpeg
    
    if '3' in choices and not has_ffmpeg:
        print(f"{Colors.RED}FFmpeg не найден! Видео не будет сохранено.{Colors.RESET}")
        print(f"{Colors.YELLOW}Установите ffmpeg для сохранения видео.{Colors.RESET}")
        time.sleep(2)
    
    return settings

def calculate_font_size(width_chars, target_width, quality='high'):
    """Рассчитывает размер шрифта для достижения целевого разрешения"""
    # Базовый расчет
    base_size = target_width // width_chars
    
    # Корректируем в зависимости от качества
    quality_multiplier = {
        'high': 2.0,
        'medium': 1.5, 
        'low': 1.0
    }
    
    font_size = int(base_size * quality_multiplier.get(quality, 1.5))
    
    # Ограничиваем разумными пределами
    font_size = max(12, min(36, font_size))
    
    return font_size

def center_ascii_content(ascii_content, target_width_chars):
    """Центрирует ASCII контент по горизонтали"""
    lines = ascii_content.split('\n')
    centered_lines = []
    
    for line in lines:
        if len(line.strip()) == 0:
            centered_lines.append('')
            continue
            
        # Вычисляем отступ для центрирования
        padding = max(0, (target_width_chars - len(line)) // 2)
        centered_line = ' ' * padding + line
        centered_lines.append(centered_line)
    
    return '\n'.join(centered_lines)

def get_video_resolution(video_path):
    """Получает разрешение исходного видео"""
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return width, height

def calculate_proper_height(width_chars, original_width, original_height):
    """Рассчитывает правильную высоту для сохранения пропорций"""
    # Сохраняем пропорции оригинала
    aspect_ratio = original_height / original_width
    proper_height_chars = int(width_chars * aspect_ratio / 2)  # /2 т.к. символы выше чем шире
    
    return max(1, proper_height_chars)

def create_ascii_for_terminal(gray_frame, width_chars, height_chars, config):
    """Создает ASCII арт для терминала с цветами"""
    ascii_chars = "@%#*+=-:. "
    color_codes = [c for k, c in ASCII_COLORS.items() if k != 'reset']
    
    ascii_lines = []
    for row in gray_frame:
        ascii_line = ""
        for pixel in row:
            if config['transparent'] and pixel > config['threshold']:
                ascii_line += " "
            else:
                char_index = min(pixel // 32, len(ascii_chars) - 1)
                char = ascii_chars[char_index]
                
                # Применяем цвет только для терминала
                if config['random_colors']:
                    color_code = color_codes[char_index % len(color_codes)]
                    ascii_line += f"{color_code}{char}{ASCII_COLORS['reset']}"
                elif config['color'] and config['color'] in ASCII_COLORS:
                    ascii_line += f"{ASCII_COLORS[config['color']]}{char}{ASCII_COLORS['reset']}"
                else:
                    ascii_line += char
        ascii_lines.append(ascii_line)
    
    return "\n".join(ascii_lines)

def create_ascii_for_save(gray_frame, width_chars, height_chars, config):
    """Создает ASCII арт для сохранения в файлы (без ANSI кодов)"""
    ascii_chars = "@%#*+=-:. "
    
    ascii_lines = []
    for row in gray_frame:
        ascii_line = ""
        for pixel in row:
            if config['transparent'] and pixel > config['threshold']:
                ascii_line += " "
            else:
                char_index = min(pixel // 32, len(ascii_chars) - 1)
                char = ascii_chars[char_index]
                ascii_line += char  # Просто символ, без цветовых кодов
        ascii_lines.append(ascii_line)
    
    return "\n".join(ascii_lines)

def video_to_ascii(video_path, config):
    """Основная функция конвертации"""
    has_ffmpeg = check_ffmpeg()
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"{Colors.RED}Ошибка открытия видео!{Colors.RESET}")
        return
    
    # Получаем информацию о видео
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    original_width, original_height = get_video_resolution(video_path)
    
    # Создаем уникальную папку для проекта
    project_path, frames_dir, video_dir = create_project_folder(video_path, config)
    
    print_header("КОНВЕРТАЦИЯ")
    print(f"{Colors.GREEN}Сохранение в: {project_path}{Colors.RESET}")
    print(f"{Colors.WHITE}Информация о видео:{Colors.RESET}")
    print(f"  FPS: {fps:.1f}")
    print(f"  Всего кадров: {total_frames}")
    print(f"  Оригинальное разрешение: {original_width}x{original_height}")
    print(f"  Цвет фона: {config['background']}")
    print(f"  Качество шрифта: {config['font_quality']}")
    
    if config['save_video'] and not has_ffmpeg:
        print(f"{Colors.RED}Внимание: FFmpeg не найден! Видео не будет сохранено.{Colors.RESET}")
        config['save_video'] = False
    
    print()
    print(f"{Colors.WHITE}Настройки:{Colors.RESET}")
    width_info = f"{config['width'] if config['width'] else 'авто'} символов"
    print(f"  Размер в терминале: {width_info}")
    
    style_parts = []
    if config['invert']:
        style_parts.append("инвертированный")
    if config['transparent']:
        style_parts.append("прозрачный фон")
    style = ", ".join(style_parts) if style_parts else "обычный"
    print(f"  Стиль: {style}")
    
    if config['transparent']:
        print(f"  Порог: {config['threshold']}")
    
    color_display = "случайные" if config['random_colors'] else config['color'] if config['color'] else "нет"
    print(f"  Цвет текста: {color_display}")
    
    save_parts = []
    if config['save_txt']:
        save_parts.append("текст")
    if config['save_frames']:
        save_parts.append("PNG")
    if config['save_video']:
        save_parts.append("видео")
    save_display = ", ".join(save_parts) if save_parts else "нет"
    print(f"  Сохранение: {save_display}")
    
    print(f"  Зацикливание: {'да' if config['loop'] else 'нет'}")
    print()
    print(f"{Colors.YELLOW}Нажмите Ctrl+C для остановки{Colors.RESET}")
    print()
    time.sleep(2)
    
    # Определяем ширину для терминала (авто или указанная)
    if config['width'] is None:
        terminal_size = shutil.get_terminal_size()
        terminal_width = terminal_size.columns - 1
    else:
        terminal_width = config['width']
    
    # Рассчитываем правильную высоту для сохранения пропорций
    terminal_height = calculate_proper_height(terminal_width, original_width, original_height)
    
    # Для сохранения видео
    temp_frames_dir = None
    if config['save_video'] and has_ffmpeg:
        temp_frames_dir = os.path.join(project_path, "temp_frames")
        if not os.path.exists(temp_frames_dir):
            os.makedirs(temp_frames_dir)
    
    try:
        clear_screen()
        frame_count = 0
        
        # Скрываем курсор
        print("\033[?25l", end='')
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                if config['loop']:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Ресайзим с сохранением пропорций
            resized = cv2.resize(gray, (terminal_width, terminal_height))
            
            if config['invert']:
                resized = 255 - resized
            
            # Создаем ASCII для терминала (с цветами)
            terminal_ascii = create_ascii_for_terminal(resized, terminal_width, terminal_height, config)
            
            # Создаем ASCII для сохранения (без цветов)
            save_ascii = create_ascii_for_save(resized, terminal_width, terminal_height, config)
            
            # Центрируем контент для терминала
            centered_content = center_ascii_content(terminal_ascii, terminal_width)
            
            # Сохранение в текстовый файл (без цветов)
            if config['save_txt']:
                txt_filename = os.path.join(frames_dir, f"frame_{frame_count:06d}.txt")
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    f.write(save_ascii)
            
            # Сохранение как изображение в оригинальном разрешении
            if config['save_frames']:
                save_ascii_as_image_original_res(save_ascii, frame_count, frames_dir, 
                                               terminal_width, terminal_height, original_width, original_height, 
                                               config)
            
            # Сохранение кадра для видео в оригинальном разрешении
            if config['save_video'] and temp_frames_dir:
                save_frame_for_video_original_res(save_ascii, frame_count, temp_frames_dir, 
                                                terminal_width, terminal_height, original_width, original_height,
                                                config)
            
            # Вывод в терминал (только ASCII арт, без лишних сообщений)
            print("\033[H" + centered_content, end='', flush=True)
            
            time.sleep(1.0 / fps if fps > 0 else 0.033)
            frame_count += 1
            
        # Показываем курсор обратно
        print("\033[?25h", end='')
        
        print(f"\n{Colors.GREEN}Готово! Сохранено {frame_count} кадров{Colors.RESET}")
        print(f"{Colors.GREEN}Файлы находятся в: {project_path}{Colors.RESET}")
        
        # Сборка видео в оригинальном разрешении
        if config['save_video'] and temp_frames_dir and has_ffmpeg:
            video_filename = f"ascii_video_{datetime.now().strftime('%H%M%S')}.mp4"
            video_output_path = os.path.join(video_dir, video_filename)
            
            success = create_video_original_res_from_frames(temp_frames_dir, video_output_path, fps)
            if success:
                print(f"{Colors.GREEN}Видео успешно сохранено: {video_output_path}{Colors.RESET}")
            else:
                print(f"{Colors.RED}Ошибка при создании видео!{Colors.RESET}")
            
    except KeyboardInterrupt:
        # Показываем курсор обратно при прерывании
        print("\033[?25h", end='')
        print(f"\n{Colors.YELLOW}Остановлено. Сохранено {frame_count} кадров{Colors.RESET}")
        print(f"{Colors.GREEN}Файлы находятся в: {project_path}{Colors.RESET}")
    finally:
        cap.release()
        # Удаляем временные файлы
        if temp_frames_dir and os.path.exists(temp_frames_dir):
            import shutil as shutil_module
            shutil_module.rmtree(temp_frames_dir)

def save_ascii_as_image_original_res(ascii_content, frame_num, output_dir, width_chars, height_chars, target_width, target_height, config):
    """Сохраняет ASCII как PNG изображение в оригинальном разрешении с центрированием"""
    try:
        import pygame
        
        # Рассчитываем размер шрифта с учетом качества
        font_size = calculate_font_size(width_chars, target_width, config['font_quality'])
        
        # Создаем поверхность с оригинальным разрешением
        img_width = target_width
        img_height = target_height
        
        pygame.init()
        
        # Используем шрифт с антиалиасингом для лучшего качества
        font = pygame.font.SysFont('Courier New', font_size, bold=True)
        surface = pygame.Surface((img_width, img_height))
        
        # Устанавливаем цвет фона
        bg_color = BACKGROUND_COLORS.get(config['background'], (0, 0, 0))
        surface.fill(bg_color)
        
        # Определяем цвет текста
        if config['color'] and config['color'] in RGB_COLORS:
            text_color = RGB_COLORS[config['color']]
        elif config['random_colors']:
            # Для случайных цветов используем белый или черный в зависимости от фона
            text_color = (255, 255, 255) if config['background'] in ['black', 'dark_gray'] else (0, 0, 0)
        else:
            # По умолчанию - белый на темном фоне, черный на светлом
            text_color = (255, 255, 255) if config['background'] in ['black', 'dark_gray'] else (0, 0, 0)
        
        lines = ascii_content.split('\n')
        
        # Рассчитываем общую высоту текста
        total_text_height = len(lines) * font_size
        
        # Центрируем по вертикали
        start_y = (img_height - total_text_height) // 2
        
        for y, line in enumerate(lines):
            if y >= height_chars:
                break
                
            text_surface = font.render(line, True, text_color)
            
            # Центрируем текст по горизонтали
            text_width = text_surface.get_width()
            x_position = (img_width - text_width) // 2
            
            # Позиция по вертикали
            y_position = start_y + y * font_size
            
            surface.blit(text_surface, (x_position, y_position))
        
        # Сохраняем PNG с максимальным качеством
        pygame.image.save(surface, os.path.join(output_dir, f"frame_{frame_num:06d}.png"))
        
    except ImportError:
        print(f"{Colors.RED}Ошибка: pygame не установлен. Установите: pip install pygame{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Ошибка при сохранении PNG: {e}{Colors.RESET}")

def save_frame_for_video_original_res(ascii_content, frame_num, output_dir, width_chars, height_chars, target_width, target_height, config):
    """Сохраняет кадр для сборки видео в оригинальном разрешении с центрированием"""
    try:
        import pygame
        
        # Используем тот же расчет что и для PNG
        font_size = calculate_font_size(width_chars, target_width, config['font_quality'])
        
        img_width = target_width
        img_height = target_height
        
        pygame.init()
        font = pygame.font.SysFont('Courier New', font_size, bold=True)
        surface = pygame.Surface((img_width, img_height))
        
        # Устанавливаем цвет фона
        bg_color = BACKGROUND_COLORS.get(config['background'], (0, 0, 0))
        surface.fill(bg_color)
        
        # Определяем цвет текста
        if config['color'] and config['color'] in RGB_COLORS:
            text_color = RGB_COLORS[config['color']]
        elif config['random_colors']:
            # Для случайных цветов используем белый или черный в зависимости от фона
            text_color = (255, 255, 255) if config['background'] in ['black', 'dark_gray'] else (0, 0, 0)
        else:
            # По умолчанию - белый на темном фоне, черный на светлом
            text_color = (255, 255, 255) if config['background'] in ['black', 'dark_gray'] else (0, 0, 0)
        
        lines = ascii_content.split('\n')
        
        # Рассчитываем общую высоту текста
        total_text_height = len(lines) * font_size
        
        # Центрируем по вертикали
        start_y = (img_height - total_text_height) // 2
        
        for y, line in enumerate(lines):
            if y >= height_chars:
                break
                
            text_surface = font.render(line, True, text_color)
            
            # Центрируем текст по горизонтали
            text_width = text_surface.get_width()
            x_position = (img_width - text_width) // 2
            
            # Позиция по вертикали
            y_position = start_y + y * font_size
            
            surface.blit(text_surface, (x_position, y_position))
        
        pygame.image.save(surface, os.path.join(output_dir, f"frame_{frame_num:06d}.png"))
        
    except ImportError:
        print(f"{Colors.RED}Ошибка: pygame не установлен{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Ошибка при сохранении кадра: {e}{Colors.RESET}")

def create_video_original_res_from_frames(frames_dir, output_video, fps):
    """Собирает видео из кадров в оригинальном разрешении"""
    try:
        print(f"{Colors.BLUE}Сборка видео...{Colors.RESET}")
        
        # Используем более надежные настройки FFmpeg
        result = subprocess.run([
            'ffmpeg', '-y',
            '-framerate', str(fps),  # Используем framerate вместо -r
            '-i', f'{frames_dir}/frame_%06d.png',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '18',  # Высокое качество
            '-preset', 'medium',
            '-r', str(fps),  # Дублируем FPS для надежности
            output_video
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        else:
            print(f"{Colors.RED}Ошибка FFmpeg: {result.stderr}{Colors.RESET}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}Ошибка при создании видео: {e}{Colors.RESET}")
        return False

def main():
    """Главная функция"""
    try:
        # Проверяем ffmpeg при старте
        if not check_ffmpeg():
            print(f"{Colors.YELLOW}Внимание: FFmpeg не найден в системе.{Colors.RESET}")
            print(f"{Colors.YELLOW}Сохранение видео будет недоступно.{Colors.RESET}")
            print(f"{Colors.BLUE}Скачайте FFmpeg с https://ffmpeg.org/{Colors.RESET}")
            print()
            input(f"{Colors.YELLOW}Нажмите Enter для продолжения...{Colors.RESET}")
        
        # Получаем путь к видео
        video_path = get_video_path()
        if not video_path:
            return
        
        # Получаем настройки
        config = display_settings_menu()
        if not config:
            return
        
        # Запускаем конвертацию
        video_to_ascii(video_path, config)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Выход из программы{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Ошибка: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
    
    input(f"\n{Colors.BLUE}Нажмите Enter для выхода...{Colors.RESET}")

if __name__ == "__main__":
    main()