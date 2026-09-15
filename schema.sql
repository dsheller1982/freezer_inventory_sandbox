CREATE TABLE IF NOT EXISTS freezer_inventory (
    id INT NOT NULL AUTO_INCREMENT,
    item_name VARCHAR(100) NOT NULL,
    quantity DECIMAL(8,2) NOT NULL,
    location VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    exp_date DATE NULL,
    PRIMARY KEY (id),
    INDEX idx_inventory_item (item_name),
    INDEX idx_inventory_location (location),
    INDEX idx_inventory_category (category),
    CONSTRAINT chk_inventory_quantity CHECK (quantity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inventory_transactions (
    id BIGINT NOT NULL AUTO_INCREMENT,
    item_id INT NULL,
    item_name VARCHAR(100) NOT NULL,
    action VARCHAR(30) NOT NULL,
    quantity_change DECIMAL(8,2) NOT NULL,
    quantity_before DECIMAL(8,2) NULL,
    quantity_after DECIMAL(8,2) NULL,
    location VARCHAR(50) NULL,
    category VARCHAR(50) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_transactions_created (created_at),
    INDEX idx_transactions_item (item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

