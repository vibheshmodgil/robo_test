package com.abstractlab.backend.service;

import com.abstractlab.backend.entity.InventoryItem;
import com.abstractlab.backend.repository.InventoryRepository;

import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class InventoryService {

    private final InventoryRepository
            inventoryRepository;

    public InventoryService(
            InventoryRepository inventoryRepository
    ) {

        this.inventoryRepository =
                inventoryRepository;
    }

    public void saveInventoryItem(
        String title,
        String description,
        String imagePath
) {

    InventoryItem inventoryItem =
            new InventoryItem();

    inventoryItem.setItemName(
            title
    );

    inventoryItem.setImagePath(
            imagePath
    );

    inventoryItem.setDescription(
            description
    );

    inventoryItem.setTimestamp(
            LocalDateTime.now()
    );

    inventoryRepository.save(
            inventoryItem
    );

    System.out.println(
            "\nINVENTORY ITEM SAVED\n"
    );

    System.out.println(
            inventoryItem.getItemName()
    );
}

public void saveDetailedInventoryItem(
        String title,
        List<String> details,
        String imagePath
) {

    String fullDescription =
            String.join(
                    "\n",
                    details
            );

    InventoryItem inventoryItem =
            new InventoryItem();

    inventoryItem.setItemName(
            title
    );

        inventoryItem.setImagePath(
                imagePath
        );

    inventoryItem.setDescription(
            fullDescription
    );

    inventoryItem.setTimestamp(
            LocalDateTime.now()
    );

    inventoryRepository.save(
            inventoryItem
    );

    System.out.println(
            "\nDETAILED INVENTORY ITEM SAVED\n"
    );

    System.out.println(
            inventoryItem.getItemName()
    );

    System.out.println(
            fullDescription
    );
}


public InventoryItem findInventoryItem(
        String itemName
) {

    itemName =
            itemName.toLowerCase();

    List<InventoryItem> items =
            inventoryRepository.findAll();

    for (
            InventoryItem item
            : items
    ) {

        String storedTitle =
                item.getItemName()
                        .toLowerCase();

        if (
            storedTitle.contains(itemName)
            ||

            itemName.contains(
                    storedTitle
            )
        ) {

            return item;
        }
    }

    return null;
}

    public List<InventoryItem>
    getAllInventoryItems() {

        return inventoryRepository.findAll();
    }
}