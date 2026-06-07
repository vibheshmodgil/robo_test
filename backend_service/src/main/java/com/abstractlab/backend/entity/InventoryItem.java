package com.abstractlab.backend.entity;

import jakarta.persistence.*;

import java.time.LocalDateTime;

@Entity
public class InventoryItem {

    @Id
    @GeneratedValue(
            strategy =
            GenerationType.IDENTITY
    )
    private Long id;

    private String itemName;

    private String imagePath;

    @Column(length = 2000)
    private String description;

    private LocalDateTime timestamp;

    public InventoryItem() {

    }

    public Long getId() {

        return id;
    }

    public String getItemName() {

        return itemName;
    }

    public void setItemName(
            String itemName
    ) {

        this.itemName =
                itemName;
    }

    public String getDescription() {

        return description;
    }

    public void setDescription(
            String description
    ) {

        this.description =
                description;
    }

    public String getImagePath() {

        return imagePath;
    }

    public void setImagePath(
            String imagePath
    ) {

        this.imagePath =
                imagePath;
    }

    public LocalDateTime getTimestamp() {

        return timestamp;
    }

    public void setTimestamp(
            LocalDateTime timestamp
    ) {

        this.timestamp =
                timestamp;
    }
}