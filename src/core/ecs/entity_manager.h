/**
 * @file entity_manager.h
 * @brief Управление сущностями и компонентами (фиксированные пулы).
 */

#ifndef ENTITY_MANAGER_H
#define ENTITY_MANAGER_H

#include "component.h"

/**
 * @brief Инициализирует менеджер сущностей (обнуляет все пулы).
 */
void entity_manager_init(void);

/**
 * @brief Создаёт новую сущность.
 * @return Идентификатор сущности (1..MAX_ENTITIES-1) или 0 при ошибке (нет свободных слотов).
 */
uint32_t create_entity(void);

/**
 * @brief Уничтожает сущность и все её компоненты.
 * @param entity Идентификатор сущности.
 */
void destroy_entity(uint32_t entity);

// --- Компонент Position ---

/**
 * @brief Проверяет, имеет ли сущность компонент Position.
 * @param entity Идентификатор сущности.
 * @return 1 если имеет, иначе 0.
 */
int has_position(uint32_t entity);

/**
 * @brief Добавляет компонент Position сущности.
 * @param entity Идентификатор сущности.
 * @param x Начальная координата X.
 * @param y Начальная координата Y.
 */
void add_position(uint32_t entity, float x, float y);

/**
 * @brief Возвращает указатель на компонент Position сущности.
 * @param entity Идентификатор сущности.
 * @return Указатель на Position или NULL, если компонент отсутствует.
 */
Position* get_position(uint32_t entity);

// --- Компонент Velocity ---

int has_velocity(uint32_t entity);
void add_velocity(uint32_t entity, float vx, float vy);
Velocity* get_velocity(uint32_t entity);

// --- Компонент Sprite ---

int has_sprite(uint32_t entity);
void add_sprite(uint32_t entity, uint8_t r, uint8_t g, uint8_t b, int w, int h);
Sprite* get_sprite(uint32_t entity);

#endif	// ENTITY_MANAGER_H