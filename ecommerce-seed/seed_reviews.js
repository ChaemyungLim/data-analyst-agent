const { faker } = require('@faker-js/faker');
const client = require('./db');
const { v4: uuidv4 } = require('uuid');

(async () => {
  await client.connect();
  console.log("Connected. Seeding reviews...");

  const resUsers = await client.query('SELECT user_id FROM users');
  const resProducts = await client.query('SELECT product_id FROM products');
  const users = resUsers.rows;
  const products = resProducts.rows;

  const usedPairs = new Set();
  let count = 0;

  while (count < 3000) {
    const user = faker.helpers.arrayElement(users);
    const product = faker.helpers.arrayElement(products);
    const key = `${user.user_id}-${product.product_id}`;
    if (usedPairs.has(key)) continue;

    usedPairs.add(key);

    await client.query(`
      INSERT INTO review (review_id, product_id, user_id, title, content)
      VALUES ($1, $2, $3, $4, $5)
    `, [
      uuidv4(),
      product.product_id,
      user.user_id,
      faker.lorem.sentence(5),
      faker.lorem.paragraph()
    ]);

    count++;
  }

  console.log("3000 reviews inserted!");
  await client.end();
})();