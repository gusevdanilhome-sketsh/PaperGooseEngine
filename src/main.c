#include <stdio.h>
#include <stdlib.h>

#ifdef USE_VULKAN
#if USE_VULKAN
#include <vulkan/vulkan.h>
#endif
#endif

int main() {
	printf("PaperGoose Engine v0.1.0\n");

#ifdef USE_VULKAN
#if USE_VULKAN
	printf("Vulkan renderer enabled\n");

	// Простая проверка Vulkan
	VkApplicationInfo appInfo = {.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
								 .pApplicationName = "PaperGoose Engine",
								 .applicationVersion = VK_MAKE_VERSION(0, 1, 0),
								 .pEngineName = "PaperGoose",
								 .engineVersion = VK_MAKE_VERSION(0, 1, 0),
								 .apiVersion = VK_API_VERSION_1_0};

	VkInstanceCreateInfo createInfo = {.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, .pApplicationInfo = &appInfo};

	VkInstance instance = 0;
	VkResult result = vkCreateInstance(&createInfo, NULL, &instance);

	if (result == VK_SUCCESS) {
		printf("Vulkan instance created successfully!\n");
		vkDestroyInstance(instance, NULL);
	} else {
		printf("Failed to create Vulkan instance. Error code: %d\n", result);
		return 1;
	}
#else
	printf("Vulkan renderer disabled (using software renderer)\n");
#endif
#else
	printf("USE_VULKAN macro not defined\n");
#endif

	printf("\n PaperGoose engine started successfully!\n");
	return 0;
}