const client = require('./db');

(async () => {
  await client.connect();
  console.log("Updating average_rating in products...");

  await client.query(`
    UPDATE products
    SET average_rating = sub.avg_rating
    FROM (
      SELECT product_id, ROUND(AVG(score)::numeric, 2) AS avg_rating
      FROM rating
      GROUP BY product_id
    ) AS sub
    WHERE products.product_id = sub.product_id
  `);

  console.log("Average ratings updated!");
  await client.end();
})();