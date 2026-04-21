CREATE TABLE users (
  user_id INT NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  PRIMARY KEY (user_id),
  UNIQUE KEY username (username),
  KEY idx_username (username)
);

CREATE TABLE categories (
  category_id INT NOT NULL AUTO_INCREMENT,
  category_name VARCHAR(50) NOT NULL,
  category_description VARCHAR(200) DEFAULT NULL,
  icon_path VARCHAR(100) DEFAULT NULL,
  display_order INT DEFAULT '0',
  is_active TINYINT(1) DEFAULT '1',
  PRIMARY KEY (category_id),
  UNIQUE KEY category_name (category_name)
);

CREATE TABLE items (
  item_id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  item_type ENUM('lost','found') NOT NULL,
  item_name VARCHAR(100) NOT NULL,
  category VARCHAR(50) NOT NULL,
  description TEXT NOT NULL,
  secret_detail VARCHAR(255) NOT NULL,
  location VARCHAR(200) NOT NULL,
  date_reported TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  status ENUM('active','claimed','returned','cancelled') DEFAULT 'active',
  image_path VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (item_id),
  KEY user_id (user_id),
  KEY idx_status (status),
  KEY idx_item_type (item_type),
  KEY idx_category (category),
  KEY idx_date_reported (date_reported),
  CONSTRAINT items_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE claims (
  claim_id INT NOT NULL AUTO_INCREMENT,
  item_id INT NOT NULL,
  claimant_id INT NOT NULL,
  secret_detail_provided TEXT NOT NULL,
  claim_status ENUM('pending','approved','rejected') DEFAULT 'pending',
  claim_date TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_date TIMESTAMP NULL DEFAULT NULL,
  notes TEXT,
  PRIMARY KEY (claim_id),
  KEY idx_claim_status (claim_status),
  KEY idx_item_id (item_id),
  KEY idx_claimant_id (claimant_id),
  CONSTRAINT claims_ibfk_1 FOREIGN KEY (item_id) REFERENCES items (item_id) ON DELETE CASCADE,
  CONSTRAINT claims_ibfk_2 FOREIGN KEY (claimant_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE messages (
  message_id INT NOT NULL AUTO_INCREMENT,
  claim_id INT NOT NULL,
  sender_id INT NOT NULL,
  receiver_id INT NOT NULL,
  message_text TEXT NOT NULL,
  sent_date TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  is_read TINYINT(1) DEFAULT '0',
  PRIMARY KEY (message_id),
  KEY receiver_id (receiver_id),
  KEY idx_claim_id (claim_id),
  KEY idx_sender_receiver (sender_id, receiver_id),
  KEY idx_sent_date (sent_date),
  CONSTRAINT messages_ibfk_1 FOREIGN KEY (claim_id) REFERENCES claims (claim_id) ON DELETE CASCADE,
  CONSTRAINT messages_ibfk_2 FOREIGN KEY (sender_id) REFERENCES users (user_id) ON DELETE CASCADE,
  CONSTRAINT messages_ibfk_3 FOREIGN KEY (receiver_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE notifications (
  notification_id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  notification_type ENUM('new_claim','claim_approved','claim_rejected','new_message','item_match') NOT NULL,
  title VARCHAR(100) NOT NULL,
  message TEXT NOT NULL,
  related_item_id INT DEFAULT NULL,
  related_claim_id INT DEFAULT NULL,
  is_read TINYINT(1) DEFAULT '0',
  created_date TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (notification_id),
  KEY related_item_id (related_item_id),
  KEY related_claim_id (related_claim_id),
  KEY idx_user_id (user_id),
  KEY idx_is_read (is_read),
  KEY idx_created_date (created_date),
  CONSTRAINT notifications_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
  CONSTRAINT notifications_ibfk_2 FOREIGN KEY (related_item_id) REFERENCES items (item_id) ON DELETE SET NULL,
  CONSTRAINT notifications_ibfk_3 FOREIGN KEY (related_claim_id) REFERENCES claims (claim_id) ON DELETE SET NULL
);
