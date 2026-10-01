-- Add company-config references to products without deleting legacy text values.
ALTER TABLE products
    ADD COLUMN uom_config_id INT NULL,
    ADD COLUMN size_config_id INT NULL,
    ADD COLUMN length_config_id INT NULL,
    ADD CONSTRAINT fk_products_uom_config
        FOREIGN KEY (uom_config_id) REFERENCES company_configs (config_id),
    ADD CONSTRAINT fk_products_size_config
        FOREIGN KEY (size_config_id) REFERENCES company_configs (config_id),
    ADD CONSTRAINT fk_products_length_config
        FOREIGN KEY (length_config_id) REFERENCES company_configs (config_id);