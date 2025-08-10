import React from 'react'
import PropTypes from 'prop-types'
import { useNavigate } from 'react-router-dom'
import Button from '@mui/material/Button'

const HomePage = (props) => {
  const { is_logged } = props
  const navigate = useNavigate()

  const on_button_click = () => {
    navigate('/login')
  }

  return (
    <div className='flex flex-col h-screen justify-center items-center m-auto space-y-6 w-8/12'>
      <p className='text-4xl font-extrabold leading-none tracking-tight text-gray-900 md:text-5xl lg:text-6xl'>Welcome to VEXGen!</p>
      <p className='text-lg font-normal text-gray-500 lg:text-xl sm:px-16 xl:px-48 dark:text-gray-400 text-center'>
        VEXGen is a simple generating tool of VEX files and assisting information supporting the creation of VEX files.
      </p>
      <div className='embed-responsive aspect-video'>
        <iframe
          title='demo-video'
          className='embed-responsive-item rounded-lg'
          width='853'
          height='480'
          src='https://www.youtube.com/embed/KPqZaauM2k0'
          allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture'
          allowFullScreen
        />
      </div>
      {is_logged ? null : <Button variant="contained" style={{backgroundColor: "#d97706"}} onClick={on_button_click}>Log In</Button>}
    </div>
  )
}

HomePage.propTypes = {
  is_logged: PropTypes.bool
}

export { HomePage }
