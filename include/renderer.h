/**
 * @file renderer.h
 * @brief Интерфейс абстрактного рендерера PaperGoose.
 * 
 * Предоставляет функции для инициализации, очистки экрана,
 * отображения кадра и завершения работы.
 */

#ifndef RENDERER_H
#define RENDERER_H

#include <GLFW/glfw3.h>
#include <stdint.h>


/**
 * @brief Инициализирует рендерер (программный растеризатор).
 * 
 * Выделяет буфер кадра (RGB, 24 бита на пиксель) и настраивает
 * OpenGL-контекст для вывода через glDrawPixels.
 * 
 * @param window  Указатель на GLFW-окно, в которое будет выводиться изображение.
 * @param width   Ширина буфера (должна совпадать с шириной окна).
 * @param height  Высота буфера (должна совпадать с высотой окна).
 * @return 0 при успехе, -1 при ошибке (выделение памяти и т.п.).
 */
int renderer_init(GLFWwindow* window, int width, int height);

/**
 * @brief Завершает работу рендерера, освобождает ресурсы.
 */
void renderer_shutdown(void);

/**
 * @brief Заполняет весь буфер кадра указанным цветом.
 * 
 * @param r Компонента красного (0–255).
 * @param g Компонента зелёного (0–255).
 * @param b Компонента синего (0–255).
 */
void renderer_clear(uint8_t r, uint8_t g, uint8_t b);

/**
 * @brief Выводит текущий буфер кадра на экран (через OpenGL).
 * 
 * Должна вызываться каждый кадр после всех отрисовок.
 */
void renderer_present(void);

#endif	// RENDERER_H