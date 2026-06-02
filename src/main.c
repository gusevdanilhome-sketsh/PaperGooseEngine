/**
 * @file main.c
 * @brief Точка входа в движок PaperGoose.
 * 
 * Выполняет инициализацию окна через GLFW, проверку доступности Vulkan
 * и запуск главного цикла обработки событий.
 */

#include <GLFW/glfw3.h>	 // GLFW для создания окна и ввода
#include <stdio.h>
#include <stdlib.h>

#ifdef USE_VULKAN
#if USE_VULKAN
#include <vulkan/vulkan.h>	// Vulkan API (только для проверки)
#endif
#endif

//==============================================================================
// Декларации вспомогательных функций
//==============================================================================

/**
 * @brief Обработчик ошибок GLFW.
 * @param error код ошибки
 * @param description текстовое описание
 */
static void glfw_error_callback(int error, const char* description);

/**
 * @brief Инициализация GLFW и создание окна.
 * @return указатель на созданное окно или NULL при ошибке
 */
static GLFWwindow* init_glfw_window(void);

/**
 * @brief Главный игровой цикл (обработка событий, рендеринг).
 * @param window указатель на окно GLFW
 */
static void main_loop(GLFWwindow* window);

/**
 * @brief Проверка работы Vulkan (создание и уничтожение instance).
 * @return 0 при успехе, иначе код ошибки (но не прерывает работу)
 */
static int test_vulkan(void);

//==============================================================================
// Реализации
//==============================================================================

/**
 * @brief Основная функция программы.
 * @return 0 при успешном завершении, иначе код ошибки
 */
int main(void) {
	printf("PaperGoose Engine v0.1.0\n");

	// 1. Тестируем Vulkan (это не критично для работы окна)
	int vulkan_status = test_vulkan();
	(void)vulkan_status;

	// 2. Инициализация GLFW и создание окна
	GLFWwindow* window = init_glfw_window();
	if (!window) {
		fprintf(stderr, "Не удалось создать окно GLFW\n");
		return 1;
	}

	// 3. Запуск главного цикла
	main_loop(window);

	// 4. Очистка ресурсов GLFW
	glfwDestroyWindow(window);
	glfwTerminate();

	printf("\nPaperGoose engine завершил работу корректно.\n");
	return 0;
}

//------------------------------------------------------------------------------
// Реализация вспомогательных функций
//------------------------------------------------------------------------------

static void glfw_error_callback(int error, const char* description) {
	fprintf(stderr, "Ошибка GLFW (%d): %s\n", error, description);
}

static GLFWwindow* init_glfw_window(void) {
	// Устанавливаем callback для ошибок
	glfwSetErrorCallback(glfw_error_callback);

	// Инициализация GLFW
	if (!glfwInit()) {
		fprintf(stderr, "Ошибка инициализации GLFW\n");
		return NULL;
	}

	// Настройки окна: отключаем изменение размера (для упрощения)
	glfwWindowHint(GLFW_RESIZABLE, GLFW_FALSE);

	// Создание окна 800x600
	GLFWwindow* window = glfwCreateWindow(800, 600, "PaperGoose Engine", NULL, NULL);
	if (!window) {
		fprintf(stderr, "Ошибка создания окна GLFW\n");
		glfwTerminate();
		return NULL;
	}

	// Делаем контекст окна текущим (нужно для событий ввода)
	glfwMakeContextCurrent(window);

	// Включаем обработку клавиш
	glfwSetInputMode(window, GLFW_STICKY_KEYS, GLFW_TRUE);

	printf("Окно успешно создано (800x600)\n");
	return window;
}

static void main_loop(GLFWwindow* window) {
	printf("Вход в главный цикл. Нажмите ESC или закройте окно для выхода.\n");

	while (!glfwWindowShouldClose(window)) {
		// Обработка событий (клавиатура, мышь, закрытие окна)
		glfwPollEvents();

		// Проверка нажатия клавиши Escape
		if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS) {
			glfwSetWindowShouldClose(window, GLFW_TRUE);
		}

		// Здесь будет происходить рендеринг (пока просто чистим экран)
		// ... (в будущем вызов Vulkan/OpenGL)
	}

	printf("Главный цикл завершён.\n");
}

static int test_vulkan(void) {
#ifdef USE_VULKAN
#if USE_VULKAN
	printf("Vulkan renderer включён. Проверка создания instance...\n");

	// Заполнение структуры информации о приложении
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
		return 0;
	} else {
		printf("  [!] Не удалось создать Vulkan instance. Код ошибки: %d\n", result);
		return 1;
	}
#else
	printf("Vulkan renderer отключён (используется софтовый рендерер).\n");
	return 0;
#endif
#else
	printf("Макрос USE_VULKAN не определён (Vulkan недоступен).\n");
	return 0;
#endif
}