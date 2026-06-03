/**
 * @file main.c
 * @brief Точка входа в движок PaperGoose.
 * 
 * Создаёт окно, инициализирует программный рендерер,
 * запускает главный цикл очистки экрана красным цветом.
 */

#include <GLFW/glfw3.h>
#include <stdio.h>
#include <stdlib.h>

#include "renderer.h"  // интерфейс рендерера

#ifdef USE_VULKAN
#if USE_VULKAN
#include <vulkan/vulkan.h>
#endif
#endif

// Вспомогательные функции (обработчик ошибок, создание окна, главный цикл)
static void glfw_error_callback(int error, const char* description);
static GLFWwindow* init_glfw_window(void);
static void main_loop(GLFWwindow* window);
static int test_vulkan(void);

//------------------------------------------------------------------------------
// Реализация
//------------------------------------------------------------------------------

int main(void) {
	printf("PaperGoose Engine v0.1.0\n");

	// 1. Проверка Vulkan (не критично)
	test_vulkan();

	// 2. Создание окна GLFW
	GLFWwindow* window = init_glfw_window();
	if (!window) {
		fprintf(stderr, "Не удалось создать окно GLFW\n");
		return 1;
	}

	// 3. Инициализация программного рендерера
	int window_width = 800;
	int window_height = 600;
	if (renderer_init(window, window_width, window_height) != 0) {
		fprintf(stderr, "Ошибка инициализации рендерера\n");
		glfwDestroyWindow(window);
		glfwTerminate();
		return 1;
	}

	// 4. Запуск главного цикла (рендеринг красного фона)
	main_loop(window);

	// 5. Очистка ресурсов
	renderer_shutdown();
	glfwDestroyWindow(window);
	glfwTerminate();

	printf("\nPaperGoose engine завершил работу корректно.\n");
	return 0;
}

static void glfw_error_callback(int error, const char* description) {
	fprintf(stderr, "Ошибка GLFW (%d): %s\n", error, description);
}

static GLFWwindow* init_glfw_window(void) {
	glfwSetErrorCallback(glfw_error_callback);
	if (!glfwInit()) {
		fprintf(stderr, "Ошибка инициализации GLFW\n");
		return NULL;
	}

	// Запрашиваем OpenGL 2.1 (минимально необходимый для glDrawPixels)
	glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 2);
	glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
	glfwWindowHint(GLFW_RESIZABLE, GLFW_FALSE);

	GLFWwindow* window = glfwCreateWindow(800, 600, "PaperGoose Engine", NULL, NULL);
	if (!window) {
		glfwTerminate();
		return NULL;
	}

	glfwMakeContextCurrent(window);
	glfwSetInputMode(window, GLFW_STICKY_KEYS, GLFW_TRUE);

	printf("Окно создано (800x600), контекст OpenGL 2.1\n");
	return window;
}

static void main_loop(GLFWwindow* window) {
	printf("Главный цикл: заполняем экран красным цветом\n");

	while (!glfwWindowShouldClose(window)) {
		glfwPollEvents();

		if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS) {
			glfwSetWindowShouldClose(window, GLFW_TRUE);
		}

		// Очистка буфера красным (255,0,0)
		renderer_clear(255, 0, 0);
		// Отображение на экране
		renderer_present();
	}
}

static int test_vulkan(void) {
#ifdef USE_VULKAN
#if USE_VULKAN
	printf("Vulkan renderer включён. Проверка создания instance...\n");
	VkApplicationInfo appInfo = {.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
								 .pApplicationName = "PaperGoose Engine",
								 .applicationVersion = VK_MAKE_VERSION(0, 1, 0),
								 .pEngineName = "PaperGoose",
								 .engineVersion = VK_MAKE_VERSION(0, 1, 0),
								 .apiVersion = VK_API_VERSION_1_0};
	VkInstanceCreateInfo createInfo = {.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, .pApplicationInfo = &appInfo};
	VkInstance instance = VK_NULL_HANDLE;
	VkResult result = vkCreateInstance(&createInfo, NULL, &instance);
	if (result == VK_SUCCESS) {
		printf("  [+] Vulkan instance создан успешно.\n");
		vkDestroyInstance(instance, NULL);
	} else
		printf("  [!] Не удалось создать Vulkan instance. Код: %d\n", result);
	return (result == VK_SUCCESS) ? 0 : 1;
#else
	printf("Vulkan renderer отключён (программный растеризатор).\n");
	return 0;
#endif
#else
	printf("Макрос USE_VULKAN не определён (Vulkan недоступен).\n");
	return 0;
#endif
}