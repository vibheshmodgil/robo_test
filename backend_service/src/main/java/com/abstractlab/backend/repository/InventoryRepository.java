package com.abstractlab.backend.repository;

import com.abstractlab.backend.entity.InventoryItem;

import org.springframework.data.jpa.repository.JpaRepository;

public interface InventoryRepository
extends JpaRepository<
        InventoryItem,
        Long
> {

}