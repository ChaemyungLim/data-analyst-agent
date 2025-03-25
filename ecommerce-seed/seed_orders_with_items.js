const { faker } = require('@faker-js/faker');
const client = require('./db');

const ORDER_COUNT = 3000;

(async () => {
  await client.connect();
  console.log("Connected. Seeding orders + order_items...");

  // user_id 목록
  const userRes = await client.query(`SELECT user_id FROM users`);
  const userIds = userRes.rows.map(row => row.user_id);

  // product 목록 (가격 포함)
  const productRes = await client.query(`SELECT product_id, price FROM products`);
  const products = productRes.rows;

  for (let i = 0; i < ORDER_COUNT; i++) {
    const orderId = faker.string.uuid();
    const userId = faker.helpers.arrayElement(userIds);
    const itemCount = faker.number.int({ min: 1, max: 5 });

    // 주문에 들어갈 상품들 (중복 없이 뽑기)
    const selectedProducts = faker.helpers.arrayElements(products, itemCount);

    let totalAmount = 0;
    const orderItems = [];

    for (const product of selectedProducts) {
      const quantity = faker.number.int({ min: 1, max: 3 });
      const unitPrice = parseFloat(product.price);
      const itemTotal = unitPrice * quantity;

      totalAmount += itemTotal;

      orderItems.push({
        order_item_id: faker.string.uuid(),
        product_id: product.product_id,
        quantity,
        unit_price: unitPrice
      });
    }

    try {
      // 1. orders 테이블 insert
      await client.query(`
        INSERT INTO orders (
          order_id, user_id, order_status, total_amount,
          discount_amount, point_used, created_at, updated_at
        ) VALUES (
          $1, $2, 'PLACED', $3, 0, 0, NOW(), NOW()
        )
      `, [orderId, userId, totalAmount]);

      // 2. order_items insert
      for (const item of orderItems) {
        await client.query(`
          INSERT INTO order_items (
            order_item_id, order_id, product_id, quantity,
            unit_price, created_at, updated_at
          ) VALUES (
            $1, $2, $3, $4, $5, NOW(), NOW()
          )
        `, [
          item.order_item_id,
          orderId,
          item.product_id,
          item.quantity,
          item.unit_price
        ]);
      }
    } catch (err) {
      console.error(`Error at order ${i}: ${err.message}`);
    }

    if (i % 500 === 0) console.log(`Inserted ${i} orders...`);
  }

  console.log("All orders + order_items inserted!");
  await client.end();
})();