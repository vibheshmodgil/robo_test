package com.abstractlab.backend.model;

public class InventoryImageResponse {

    private boolean success;

    private String imagePath;

    public boolean isSuccess() {
        return success;
    }

    public void setSuccess(
            boolean success
    ) {
        this.success = success;
    }

    public String getImagePath() {
        return imagePath;
    }

    public void setImagePath(
            String imagePath
    ) {
        this.imagePath = imagePath;
    }
}