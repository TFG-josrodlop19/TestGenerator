import React, { useState, useEffect } from 'react'
import { styled } from '@mui/material/styles'
import { useParams } from 'react-router'
import PropTypes from 'prop-types'
import Checkbox from '@mui/material/Checkbox'
import ArrowForwardIosSharpIcon from '@mui/icons-material/ArrowForwardIosSharp'
import MuiAccordion from '@mui/material/Accordion'
import MuiAccordionSummary from '@mui/material/AccordionSummary'
import MuiAccordionDetails from '@mui/material/AccordionDetails'
import Typography from '@mui/material/Typography'
import { Plus, Minus, BadgeCheck, BadgeAlert } from 'lucide-react'

const ReadMore = ({ id, text, amountOfWords = 36 }) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const splittedText = text.split(' ')
  const itCanOverflow = splittedText.length > amountOfWords
  const beginText = itCanOverflow
    ? splittedText.slice(0, amountOfWords - 1).join(' ')
    : text
  const endText = splittedText.slice(amountOfWords - 1).join(' ')
  
  const handleKeyboard = (e) => {
    if (e.code === 'Space' || e.code === 'Enter') {
      setIsExpanded(!isExpanded)
    }
  }

  return (
    <span id={id}>
      {beginText}
      {itCanOverflow && (
        <>
          {!isExpanded && <span>... </span>}
          <span 
            className={`${!isExpanded && 'hidden'}`} 
            aria-hidden={!isExpanded}
          >
            {endText}
          </span>
          <span
            className='text-violet-400 ml-2'
            role="button"
            tabIndex={0}
            aria-expanded={isExpanded}
            aria-controls={id}
            onKeyDown={handleKeyboard}
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'show less' : 'show more'}
          </span>
        </>
      )}
    </span>
  )
}

ReadMore.propTypes = {
  id: PropTypes.string,
  text: PropTypes.string,
  amountOfWords: PropTypes.number
}

const Accordion = styled((props) => (
  <MuiAccordion disableGutters elevation={0} square {...props} />
))(({ theme }) => ({
  border: `1px solid ${theme.palette.divider}`,
  '&:not(:last-child)': {
    borderBottom: 0,
  },
  '&::before': {
    display: 'none',
  },
}))

const AccordionSummary = styled((props) => (
  <MuiAccordionSummary
    expandIcon={<ArrowForwardIosSharpIcon sx={{ fontSize: '0.9rem' }} />}
    {...props}
  />
))(({ theme }) => ({
  backgroundColor:
    theme.palette.mode === 'dark'
      ? 'rgba(255, 255, 255, .05)'
      : 'rgba(0, 0, 0, .03)',
  flexDirection: 'row-reverse',
  '& .MuiAccordionSummary-expandIconWrapper.Mui-expanded': {
    transform: 'rotate(90deg)',
  },
  '& .MuiAccordionSummary-content': {
    marginLeft: theme.spacing(1),
  },
}))

const AccordionDetails = styled(MuiAccordionDetails)(({ theme }) => ({
  padding: theme.spacing(2),
  borderTop: '1px solid rgba(0, 0, 0, .125)',
}))


const ShowVEXPage = () => {
  const params = useParams()
  const [vex, set_vex] = useState([])
  const [statements, set_statments] = useState([])
  const [expanded, setExpanded] = useState('')
  const [show_cvss, set_show_cvss] = useState(false)
  const [show_cwes, set_show_cwes] = useState(false)
  const [show_exploits, set_show_exploits] = useState(false)
  const [show_reachable_code, set_show_reachable_code] = useState(false)

  const handle_change = (panel) => (event, newExpanded) => {
    setExpanded(newExpanded ? panel : false)
  }

  const on_click_show_cvss = () => {
    set_show_cvss(!show_cvss)
  }

  const on_click_show_cwes = () => {
    set_show_cwes(!show_cwes)
  }

  const on_click_show_exploits = () => {
    set_show_exploits(!show_exploits)
  }

  const on_click_show_reachable_code = () => {
    set_show_reachable_code(!show_reachable_code)
  }

  useEffect(() => {
    const access_token = localStorage.getItem('access_token')
    fetch('http://localhost:8000/vex/show/' + params.id, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${access_token}`
      }
    })
      .then((r) => r.json())
      .then((r) => {
        set_vex(r)
        set_statments(r.extended_vex.extended_statements)
      })
  }, [params.id])

  return (
    <div className='flex flex-col h-screen justify-center m-auto w-8/12'>
      <div className='flex'>
        <p className='flex text-gray-400 border-t-2 border-b-2 border-l-2'>Show extended information:&ensp;<Plus size={20} className='text-lime-500'/>&ensp;|&ensp;</p>
        <p className='flex text-gray-400 border-t-2 border-b-2'>Completed statements:&ensp;<BadgeCheck size={20} className='text-blue-500'/>&ensp;|&ensp;</p>
        <p className='flex text-gray-400 border-t-2 border-b-2 border-r-2'>Incompleted statements:&ensp;<BadgeAlert size={20} className='text-red-500'/></p>
      </div>
      <p className='mt-2 mb-2 text-lg font-normal text-gray-500 lg:text-xl sm:px-16 xl:px-48 dark:text-gray-400 text-center'>
        {vex.owner}/{vex.name}: {vex.sbom_path}
      </p>
      {statements.map((statement, index) => (
        <Accordion className='w-full' key={index} expanded={expanded === 'panel'+index} onChange={handle_change('panel'+index)}>
          <AccordionSummary aria-controls="panel1d-content" id="panel1d-header">
            <Typography className='flex'>Statement {index}&ensp;{statement.status === "Go to VEX Extended file to find vulnerability assisted information." ? <BadgeAlert size={20} className='text-red-500'/> : <BadgeCheck size={20} className='text-blue-500'/>}</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography>
              <span>- Vulnerability:<br /></span>
              <span>&ensp;&ensp;&ensp;{'\u2022'} Name: <a className='underline text-blue-600 hover:text-blue-800 visited:text-purple-600' href={statement.vulnerability["@id"]}>{statement.vulnerability.name}</a><br /></span> 
              <span>&ensp;&ensp;&ensp;{'\u2022'} Description: <ReadMore id="read-more-text" text={statement.vulnerability.description} /><br /></span>
              <span>&ensp;&ensp;&ensp;{'\u2022'} CVSS:<Checkbox color={show_cvss ? "error": "success"} icon={<Plus size={20} className='text-lime-500 rounded-full'/>} checkedIcon={<Minus size={20} className='text-red-500 rounded-full'/>} onClick={on_click_show_cvss}/><br /></span>
              { show_cvss ?
                <>
                  <span>&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;{'\u22c4'} Vulnerability Impact: {statement.vulnerability.cvss.vuln_impact}<br /></span>
                  <span>&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;{'\u22c4'} CVSS version: {statement.vulnerability.cvss.version}<br /></span>
                  <span>&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;{'\u22c4'} Attack Vector: {statement.vulnerability.cvss.attack_vector}<br /></span> 
                </> :
                null
              }
              <span>&ensp;&ensp;&ensp;{'\u2022'} CWEs:<Checkbox color={show_cwes ? "error": "success"} icon={<Plus size={20} className='text-lime-500 rounded-full'/>} checkedIcon={<Minus size={20} className='text-red-500 rounded-full'/>} onClick={on_click_show_cwes}/><br /></span>
              { show_cwes ?
                statement.vulnerability.cwes && statement.vulnerability.cwes.map(
                  (cwe, index) => (
                    <span key={index}>&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;{'\u22c4'} CWE {index}: <a className='underline text-blue-600 hover:text-blue-800 visited:text-purple-600' href={cwe["@id"]}>CWE-{cwe.name}</a><br /></span> 
                  )
                )
                :
                null
              }
              <span>- Status: {statement.status}<br /></span>
              <span>- Justification: {statement.justification}<br /></span>
              <span>- Supplier: {statement.supplier}<br /></span>
              <span>- Exploits:<Checkbox color={show_exploits ? "error": "success"} icon={<Plus size={20} className='text-lime-500 rounded-full'/>} checkedIcon={<Minus size={20} className='text-red-500 rounded-full'/>} onClick={on_click_show_exploits}/><br /></span>
              { show_exploits ?
                statement.exploits && statement.exploits
                .filter(exploit => exploit["@id"] !== "Unknown")
                .map(
                  (exploit, index) => (
                    <span key={index}>&ensp;&ensp;&ensp;{'\u2022'} Exploit {index}: <a className='underline text-blue-600 hover:text-blue-800 visited:text-purple-600' href={exploit["@id"]}>{exploit["@id"]}</a><br /></span> 
                  )
                )
                :
                null
              }
              <span>- Reachable Code:<Checkbox color={show_reachable_code ? "error": "success"} icon={<Plus size={20} className='text-lime-500 rounded-full'/>} checkedIcon={<Minus size={20} className='text-red-500 rounded-full'/>} onClick={on_click_show_reachable_code}/><br /></span>
              { show_reachable_code ?
                statement.reachable_code && statement.reachable_code.map(
                  (reachable_code) => (
                    <span key={index}>&ensp;&ensp;&ensp;{'\u2022'} Reachable code in path {reachable_code.path_to_file} with: {
                        reachable_code.used_artifacts.map((artifact, index) => (
                          <p key={index}>
                            &ensp;&ensp;&ensp;&ensp;&ensp;&ensp;{'\u22c4'} Artifact {artifact.artifact_name} in lines {artifact.used_in_lines.join(', ')}.
                          </p>
                        ))
                      }
                      <br />
                    </span> 
                  )
                )
                :
                null
              }
            </Typography>
          </AccordionDetails>
        </Accordion>
      ))}
    </div>
  )
}

export { ShowVEXPage }
