print('=== S3 年月借阅趋势（按 %Y-%m 分组）===');
const t = db.borrow_logs.aggregate([
  { $group: { _id: { $dateToString: { format: '%Y-%m', date: '$borrow_date', timezone: '+08:00' } }, n: { $sum: 1 } } },
  { $sort: { _id: 1 } }
]).toArray();
print('月数: ' + t.length + '，区间 ' + t[0]._id + ' 至 ' + t[t.length - 1]._id);
printjson(t.slice(0, 2));
print('=== S4 借阅 Top3（含馆藏位置）===');
printjson(db.borrow_logs.aggregate([
  { $group: { _id: '$book_isbn', n: { $sum: 1 } } },
  { $sort: { n: -1 } }, { $limit: 3 },
  { $lookup: { from: 'books', localField: '_id', foreignField: 'isbn', as: 'b' } },
  { $unwind: '$b' },
  { $project: { _id: 0, title: '$b.title', location: '$b.location', borrow_count: '$n' } }
]).toArray());
