const { faker } = require('@faker-js/faker');
const client = require('./db');

(async () => {
  await client.connect();
  console.log("Connected. Seeding cart...");

  const userRes = await client.query('SELECT user_id FROM users');
  const productRes = await client.query('SELECT product_id FROM products');
  const users = userRes.rows;
  const products = productRes.rows;

  // 전체 유저 중 30%만 선택
  const sampledUsers = faker.helpers.arrayElements(users, Math.floor(users.length * 0.3));

  for (const user of sampledUsers) {
    const productCount = faker.number.int({ min: 1, max: 5 });
    const sampledProducts = faker.helpers.arrayElements(products, productCount);

    for (const product of sampledProducts) {
      await client.query(`
        INSERT INTO cart (cart_id, user_id, product_id, quantity)
        VALUES ($1, $2, $3, $4)
      `, [
        faker.string.uuid(),
        user.user_id,
        product.product_id,
        faker.number.int({ min: 1, max: 10 })
      ]);
    }
  }

  console.log("Cart seeded successfully.");
  await client.end();
})();