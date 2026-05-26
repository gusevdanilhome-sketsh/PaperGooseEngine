/**
 * @file window.h
 * @brief Обёртка над созданием окна и контекстом SDL2.
 */

#ifndef WINDOW_H
#define WINDOW_H

#include <SDL.h>
#include <stdbool.h>

/**
 * @brief Основная структура окна приложения.
 */
typedef struct {
	SDL_Window* sdl_window;		/**< Указатель на окно SDL. */
	SDL_Renderer* sdl_renderer; /**< Указатель на рендерер SDL. */
	int width;					/**< Ширина окна в пикселях. */
	int height;					/**< Высота окна в пикселях. */
	bool should_close;			/**< Флаг закрытия окна. */
} window_t;

/**
 * @brief Создать окно с заданными параметрами.
 * @param[in] title Заголовок окна.
 * @param[in] width Ширина.
 * @param[in] height Высота.
 * @return Указатель на структуру окна или NULL при ошибке.
 */
window_t* window_create(const char* title, int width, int height);

/**
 * @brief Уничтожить окно и освободить ресурсы SDL.
 * @param[in] win Указатель на окно.
 */
void window_destroy(window_t* win);

/**
 * @brief Обработать очередь событий SDL (клавиши, закрытие).
 * @param[in] win Указатель на окно.
 */
void window_poll_events(window_t* win);

/**
 * @brief Очистить экран заданным цветом.
 * @param[in] win Указатель на окно.
 * @param[in] r Красный (0-255).
 * @param[in] g Зелёный.
 * @param[in] b Синий.
 */
void window_clear(const window_t* win, uint8_t r, uint8_t g, uint8_t b);

/**
 * @brief Показать нарисованное на экране (swap buffers).
 * @param[in] win Указатель на окно.
 */
void window_present(window_t* win);

#endif /* WINDOW_H */