const { faker } = require('@faker-js/faker');
const client = require('./db');

(async () => {
  await client.connect();
  console.log("Connected. Seeding inventory...");

  const result = await client.query('SELECT product_id FROM products');
  const products = result.rows;

  for (const p of products) {
    await client.query(`
      INSERT INTO inventory (inventory_id, product_id, quantity)
      VALUES ($1, $2, $3)
    `, [
      faker.string.uuid(),
      p.product_id,
      faker.number.int({ min: 0, max: 1000 })
    ]);
  }

  console.log("Inventory seeded successfully.");
  await client.end();
})();