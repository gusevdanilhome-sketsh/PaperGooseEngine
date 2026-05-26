/**
 * @file resource.h
 * @brief Простейший менеджер текстур на основе SDL2_image.
 */

#ifndef RESOURCE_H
#define RESOURCE_H

#include <SDL.h>
#include <stdint.h>

/** Максимальное количество загружаемых текстур. */
enum { RESOURCE_MAX_TEXTURES = 256 };

/**
 * @brief Менеджер текстур.
 */
typedef struct {
	SDL_Texture* textures[RESOURCE_MAX_TEXTURES]; /**< Массив текстур. */
	int count;									  /**< Текущее количество загруженных текстур. */
	SDL_Renderer* renderer;						  /**< Ссылка на рендерер SDL. */
} resource_manager_t;

/**
 * @brief Создать и инициализировать менеджер текстур.
 * @param[in] renderer Указатель на SDL_Renderer.
 * @return Указатель на менеджер или NULL при ошибке.
 */
resource_manager_t* resource_manager_create(SDL_Renderer* renderer);

/**
 * @brief Уничтожить менеджер и все текстуры.
 * @param[in] manager Указатель на менеджер.
 */
void resource_manager_destroy(resource_manager_t* manager);

/**
 * @brief Загрузить текстуру из файла и получить её идентификатор.
 * @param[in] manager Указатель на менеджер.
 * @param[in] path Путь к файлу изображения (PNG и др.).
 * @return Идентификатор текстуры (0 при ошибке, 0 зарезервирован).
 */
int resource_texture_load(resource_manager_t* manager, const char* path);

/**
 * @brief Получить SDL_Texture по идентификатору.
 * @param[in] manager Указатель на менеджер.
 * @param[in] id Идентификатор текстуры.
 * @return Указатель на SDL_Texture или NULL.
 */
SDL_Texture* resource_texture_get(const resource_manager_t* manager, int id);

#endif /* RESOURCE_H */