/**
 * @file ecs.h
 * @brief Ядро ECS (Entity Component System) на разреженных множествах.
 */

#ifndef ECS_H
#define ECS_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


/** Максимальное количество сущностей (константа через enum). */
enum { ECS_MAX_ENTITIES = 10000 };

/** Максимальное число типов компонентов. */
enum { ECS_MAX_COMPONENT_TYPES = 64 };

/** Идентификатор сущности. */
typedef uint32_t ecs_entity_t;

/** Идентификатор типа компонента. */
typedef uint32_t ecs_component_type_t;

/**
 * @brief Пул компонентов одного типа.
 */
typedef struct {
	void* components;				 /**< Указатель на массив компонентов (каждый размером component_size). */
	size_t component_size;			 /**< Размер одного компонента в байтах. */
	bool presence[ECS_MAX_ENTITIES]; /**< Маска присутствия компонента у сущности. */
} ecs_component_pool_t;

/**
 * @brief Мир ECS, управляющий всеми сущностями и компонентами.
 */
typedef struct {
	ecs_component_pool_t pools[ECS_MAX_COMPONENT_TYPES]; /**< Пулы компонентов по типам. */
	bool entity_alive[ECS_MAX_ENTITIES];				 /**< Флаг существования сущности. */
	uint64_t entity_mask[ECS_MAX_ENTITIES];				 /**< Битовая маска типов компонентов сущности. */
	ecs_entity_t next_entity;							 /**< Следующий свободный идентификатор сущности. */
} ecs_world_t;

/**
 * @brief Создать новый мир ECS.
 * @return Указатель на мир или NULL при ошибке.
 */
ecs_world_t* ecs_world_create(void);

/**
 * @brief Уничтожить мир и освободить ресурсы.
 * @param[in] world Указатель на мир.
 */
void ecs_world_destroy(ecs_world_t* world);

/**
 * @brief Создать новую сущность в мире.
 * @param[in] world Указатель на мир.
 * @return Идентификатор сущности или 0 при ошибке (0 зарезервирован).
 */
ecs_entity_t ecs_entity_create(ecs_world_t* world);

/**
 * @brief Уничтожить сущность и удалить все её компоненты.
 * @param[in] world Указатель на мир.
 * @param[in] entity Идентификатор сущности.
 */
void ecs_entity_destroy(ecs_world_t* world, ecs_entity_t entity);

/**
 * @brief Зарегистрировать новый тип компонента.
 * @param[in] world Указатель на мир.
 * @param[in] comp_size Размер структуры компонента в байтах.
 * @return Идентификатор типа компонента или ECS_MAX_COMPONENT_TYPES при переполнении.
 */
ecs_component_type_t ecs_component_register(ecs_world_t* world, size_t comp_size);

/**
 * @brief Добавить компонент сущности и вернуть указатель на данные.
 * @param[in] world Указатель на мир.
 * @param[in] entity Идентификатор сущности.
 * @param[in] type Идентификатор типа компонента.
 * @return Указатель на компонент или NULL при ошибке.
 */
void* ecs_component_add(ecs_world_t* world, ecs_entity_t entity, ecs_component_type_t type);

/**
 * @brief Получить указатель на компонент сущности.
 * @param[in] world Указатель на мир.
 * @param[in] entity Идентификатор сущности.
 * @param[in] type Идентификатор типа компонента.
 * @return Указатель на компонент или NULL, если отсутствует.
 */
void* ecs_component_get(const ecs_world_t* world, ecs_entity_t entity, ecs_component_type_t type);

/**
 * @brief Удалить компонент у сущности.
 * @param[in] world Указатель на мир.
 * @param[in] entity Идентификатор сущности.
 * @param[in] type Идентификатор типа компонента.
 */
void ecs_component_remove(ecs_world_t* world, ecs_entity_t entity, ecs_component_type_t type);

#endif /* ECS_H */