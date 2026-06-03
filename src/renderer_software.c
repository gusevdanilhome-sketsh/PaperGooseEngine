/**
 * @file renderer_software.c
 * @brief Программный растеризатор (заглушка) для PaperGoose.
 * 
 * Реализует интерфейс renderer.h, используя буфер в оперативной памяти
 * и вывод через glDrawPixels (OpenGL 1.x).
 */

#include <GL/gl.h>	// OpenGL 1.x функции (glDrawPixels, glRasterPos2i)
#include <stdlib.h>
#include <string.h>

#include "renderer.h"

static GLFWwindow* g_window = NULL;	 // Сохраняем окно для получения размеров
static int g_width = 0;
static int g_height = 0;
static uint8_t* g_framebuffer = NULL;  // Буфер в формате RGBRGB...

int renderer_init(GLFWwindow* window, int width, int height) {
	if (!window || width <= 0 || height <= 0) {
		return -1;
	}

	g_window = window;
	g_width = width;
	g_height = height;

	// Выделяем память под буфер (3 байта на пиксель: R, G, B)
	g_framebuffer = (uint8_t*)malloc(3 * width * height);
	if (!g_framebuffer) {
		g_window = NULL;
		return -1;
	}

	// Настраиваем OpenGL: пиксельная точность, отключаем билинейную фильтрацию
	glPixelStorei(GL_UNPACK_ALIGNMENT, 1);	// Выравнивание по байтам
	glRasterPos2i(-1, -1);					// Растянуть на всё окно (ортографический диапазон [-1,1])
	glPixelZoom((GLfloat)width / width,
				(GLfloat)height / height);	// Коэффициенты масштабирования (1:1)

	// Устанавливаем область просмотра (viewport) равной размерам окна
	glViewport(0, 0, width, height);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	glOrtho(-1, 1, -1, 1, -1, 1);  // Ортогональная проекция для точного пиксельного вывода
	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();

	// Изначально очищаем буфер чёрным (на всякий случай)
	renderer_clear(0, 0, 0);

	return 0;
}

void renderer_shutdown(void) {
	if (g_framebuffer) {
		free(g_framebuffer);
		g_framebuffer = NULL;
	}
	g_window = NULL;
}

void renderer_clear(uint8_t r, uint8_t g, uint8_t b) {
	if (!g_framebuffer) {
		return;
	}

	// Заполняем буфер одним цветом (по 3 байта на пиксель)
	size_t pixel_count = g_width * g_height;
	for (size_t i = 0; i < pixel_count; ++i) {
		g_framebuffer[i * 3 + 0] = r;
		g_framebuffer[i * 3 + 1] = g;
		g_framebuffer[i * 3 + 2] = b;
	}
}

void renderer_present(void) {
	if (!g_framebuffer || !g_window) {
		return;
	}

	// Делаем OpenGL-контекст текущим (на случай, если несколько окон)
	glfwMakeContextCurrent(g_window);

	// Выводим буфер на экран
	glDrawPixels(g_width, g_height, GL_RGB, GL_UNSIGNED_BYTE, g_framebuffer);

	// Меняем передний и задний буферы (двойная буферизация GLFW)
	glfwSwapBuffers(g_window);
}