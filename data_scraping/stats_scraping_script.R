library(baseballr)
library(tidyverse)

get_dates = function(start, end) {
  
  dates = seq(as.Date(start), as.Date(end), by="days")
  
  return(as.character(dates))
}

get_statcast_data = function(dates, hitter=TRUE) {
  
  n_queries = ceiling(length(dates) / 5)
  n = length(dates)
  df = NULL
  for (i in 0:(n_queries - 1)) {
    first = i * 5 + 1
    last = (i + 1) * 5
    
    if (last > n) {
      last = n
    }
    
    first_date = dates[first]
    last_date = dates[last]
    
    print(first_date)
    
    statcast = NULL
    tryCatch({
      if (hitter) {
        statcast = statcast_search_batters(start_date = first_date,
                                           end_date = last_date)
      } else {
        statcast = statcast_search_pitchers(start_date = first_date,
                                            end_date = last_date)
      }
      
      df = rbind(df, statcast)
    }, error = function(e) {
      # Handle the error gracefully
      # For example, print an error message and continue execution
      cat("An error occurred:", conditionMessage(e), "\n")
    })
    
    
  }
  
  return(df)
}


load_and_save_statcast = function(year, first_day, last_day) {
  dates = get_dates(first_day, last_day)
  
  hitter = get_statcast_data(dates, TRUE)
  pitcher = get_statcast_data(dates, FALSE)
  
  hitter_file = paste("hitter_statcast_", year, ".rdata")
  save(hitter, file = hitter_file)
  
  pitcher_file = paste("pitcher_statcast_", year, ".rdata")
  save(pitcher, file = pitcher_file)
}

load_and_save_statcast(2015, "2015-4-5", "2015-10-4")
load_and_save_statcast(2016, "2016-4-3", "2016-10-2")
load_and_save_statcast(2017, "2017-4-2", "2017-10-1")
load_and_save_statcast(2018, "2018-3-29", "2018-10-1")
load_and_save_statcast(2019, "2019-3-20", "2019-9-29")
load_and_save_statcast(2020, "2020-7-23", "2020-9-27")
load_and_save_statcast(2021, "2021-4-1", "2021-10-3")