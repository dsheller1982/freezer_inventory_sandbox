DELETE FROM inventory_transactions;
DELETE FROM freezer_inventory;

INSERT INTO freezer_inventory (item_name, quantity, location, category, exp_date) VALUES
('80/20 Ground Beef', 8, 'Upright Freezer A', 'Beef', '2027-02-15'),
('Chuck Roast', 3, 'Upright Freezer A', 'Beef', '2027-01-20'),
('Ribeye Steaks', 4, 'Upright Freezer B', 'Beef', '2026-12-10'),
('Pork Shoulder', 2, 'Upright Freezer A', 'Pork', '2027-03-01'),
('Baby Back Ribs', 3, 'Upright Freezer B', 'Pork', '2027-02-08'),
('Bacon', 6, 'Upright Freezer B', 'Pork', '2026-11-18'),
('Chicken Breasts', 10, 'Upright Freezer A', 'Chicken', '2027-01-05'),
('Chicken Thighs', 7, 'Upright Freezer A', 'Chicken', '2027-01-12'),
('Whole Turkey', 1, 'Upright Freezer B', 'Poultry', '2027-04-01'),
('Italian Sausage', 5, 'Upright Freezer B', 'Pork', '2026-12-22'),
('Mixed Vegetables', 4, 'Upright Freezer A', 'Vegetables', '2026-10-30'),
('French Fries', 3, 'Upright Freezer B', 'Prepared Foods', '2026-11-15'),
('Homemade Chili', 5, 'Upright Freezer A', 'Prepared Foods', '2026-10-20'),
('Pizza Dough', 6, 'Upright Freezer B', 'Prepared Foods', '2026-10-12'),
('Blueberries', 4, 'Upright Freezer A', 'Fruit', '2027-01-25');

INSERT INTO inventory_transactions
(item_id, item_name, action, quantity_change, quantity_before, quantity_after, location, category)
VALUES (NULL, 'Demo dataset', 'reset', 0, NULL, NULL, NULL, NULL);
