const { faker } = require('@faker-js/faker');
const client = require('./db');

(async () => {
  await client.connect();
  console.log("Connected. Seeding user_coupons...");

  const resUsers = await client.query('SELECT user_id FROM users');
  const resCoupons = await client.query('SELECT coupon_id FROM coupon');

  const users = resUsers.rows.map(row => row.user_id);
  const coupons = resCoupons.rows.map(row => row.coupon_id);

  const assignments = [];

  for (const coupon_id of coupons) {
    const sampledUsers = faker.helpers.arrayElements(users, 100); // 쿠폰당 100명에게 발급

    for (const user_id of sampledUsers) {
      assignments.push({
        id: faker.string.uuid(),
        user_id,
        coupon_id,
        assigned_at: faker.date.recent({ days: 30 }),
        is_used: false,
      });
    }
  }

  for (const u of assignments) {
    await client.query(`
      INSERT INTO user_coupons (
        id, user_id, coupon_id, assigned_at, is_used
      ) VALUES ($1, $2, $3, $4, $5)
    `, [
      u.id,
      u.user_id,
      u.coupon_id,
      u.assigned_at,
      u.is_used
    ]);
  }

  console.log("All user_coupons inserted!");
  await client.end();
})();