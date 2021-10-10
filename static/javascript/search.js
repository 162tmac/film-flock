var search = document.getElementById('film-search-container')

filterFilms = function (films) {
  var formInput = document.getElementById('film-search').value
  if (formInput.length == 0 || formInput == '') return []
  console.log(films)
  console.log(
    films.filter((films) => {
      films.title.toLower().includes(formInput.toLower())
    })
  )
}
